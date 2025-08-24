# app/sse_manager.py
import queue

class SseManager:
    def __init__(self):
        self.message_queue = queue.Queue()

    def listen(self):
        try:
            while True:
                msg = self.message_queue.get()
                yield msg
        except GeneratorExit:
            print("Client disconnected.")

    def publish(self, msg):
        self.message_queue.put(msg)
