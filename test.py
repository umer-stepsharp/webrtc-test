from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports import smallwebrtc
import inspect

print("PipelineRunner.__init__ signature:")
print(inspect.signature(PipelineRunner.__init__))

print("\nPipelineRunner methods:")
print([m for m in dir(PipelineRunner) if not m.startswith("_")])

print("SmallWebRTCTransport dir:", dir(smallwebrtc))
