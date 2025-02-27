import pyaudio
import speech_recognition as sr
import threading
import collections
import time

class Recording:
    def __init__(self, rate=16000, chunk=1024):
        self.chunk = chunk
        self.rate = rate
        self.frames = collections.deque()  # Queue for real-time streaming
        self.running = True
        self.audio = pyaudio.PyAudio()

        # Open pyaudio stream
        self.stream = self.audio.open(format=pyaudio.paInt16, 
                                      channels=1, 
                                      rate=self.rate, 
                                      input=True, 
                                      frames_per_buffer=self.chunk)

    def record(self):
        print("🎤 Listening... Speak into the microphone (Press Ctrl+C to stop)")
        while self.running:
            try:
                # Read audio data from the stream
                data = self.stream.read(self.chunk)
                self.frames.append(data)  # Store audio frames
            except Exception as e:
                print(f"⚠️ Error while recording: {e}")
    
    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()


class Processing:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.command_event = threading.Event()  # Event for detected commands

    def process_audio(self, batch):
        try:
            print("🔄 Processing batch...")

            # Convert frames to an AudioData object
            combined_audio = b"".join(batch)  # Combine frames
            audio_data = sr.AudioData(combined_audio, 16000, 2)  # 16kHz sample rate, 2 bytes per sample (16-bit)

            # Recognize speech using Google Web Speech API
            text = self.recognizer.recognize_google(audio_data)
            print(f"📝 Transcribed: {text}")

            # Process recognized command for the robot
            self.process_command(text)

        except sr.UnknownValueError:
            print("⚠️ Could not understand the audio.")
        except sr.RequestError as e:
            print(f"⚠️ Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            print(f"⚠️ Error during transcription: {e}")

    def process_command(self, text):
        """Process recognized text and send robot commands"""
        commands = {
            "start": "🤖 Robot is starting...",
            "stop": "🛑 Robot is stopping...",
            "move forward": "⬆️ Robot moving forward...",
            "move backward": "⬇️ Robot moving backward...",
            "turn left": "⬅️ Robot turning left...",
            "turn right": "➡️ Robot turning right..."
        }

        for command, action in commands.items():
            if command in text.lower():
                print(f"✅ Command detected: {command.upper()}")
                print(action)
                self.command_event.set()  # Trigger event

    def run(self, recording_instance):
        try:
            batch = collections.deque()  # Store batches
            start_time = time.time()
            while recording_instance.running:
                if len(recording_instance.frames) > 0:
                    batch.append(recording_instance.frames.popleft())

                # Process batch every 5 seconds
                if time.time() - start_time >= 5 and batch:
                    self.process_audio(batch)
                    batch.clear()  # Clear batch after processing
                    start_time = time.time()  # Reset timer

        except KeyboardInterrupt:
            print("\n🛑 Stopping processing...")


if __name__ == "__main__":
    recording = Recording(rate=16000, chunk=1024)
    processing = Processing()

    # Create threads for recording and processing
    recording_thread = threading.Thread(target=recording.record)
    processing_thread = threading.Thread(target=processing.run, args=(recording,))

    # Start the threads
    recording_thread.start()
    processing_thread.start()

    # Wait for threads to finish
    recording_thread.join()
    processing_thread.join()

    # Stop the recording after processing
    recording.stop()
