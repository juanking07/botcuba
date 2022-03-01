class Progress:
    def __init__(self, chunk_size = 1024 * 1024):
        self.actual = 0
        self.chunk_iter = 0
        self.chunk_size = chunk_size
        self.chunk_callback = self.chunk_callback
        self.bar = None

    def chunk_callback(self, *args, **kwargs):
        self.bar.next(self.chunk_iter)

    def callback(self, *args, **kwargs):
        b = args[0].bytes_read
        self.chunk_iter += b - self.actual
        self.actual = b

        if self.chunk_iter >= self.chunk_size:
            self.chunk_callback(b, monitor = args[0], **kwargs)
            self.chunk_iter = 0
