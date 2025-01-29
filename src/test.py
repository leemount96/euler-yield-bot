from processor.processor import Processor

processor = Processor([1, 8453, 1923], 1_000_000)
print(processor.generate_merkl_opportunities_message(5))
print(processor.generate_euler_opportunities_message(5))