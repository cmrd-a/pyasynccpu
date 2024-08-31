import asyncio
import logging
import grpc
from grpc_reflection.v1alpha import reflection
import helloworld_pb2
import helloworld_pb2_grpc
import concurrent.futures

_cleanup_coroutines = []


def cpu_bound():
    return sum(i * i for i in range(10**8))


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    async def SayHello(self,request: helloworld_pb2.HelloRequest,context: grpc.aio.ServicerContext) -> helloworld_pb2.HelloReply:
        with concurrent.futures.ProcessPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, cpu_bound)
            print(result)
        return helloworld_pb2.HelloReply(message="Hello, %s!" % result)


async def serve() -> None:
    server = grpc.aio.server()
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    SERVICE_NAMES = (
        helloworld_pb2.DESCRIPTOR.services_by_name["Greeter"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port("[::]:50051")
    await server.start()

    async def server_graceful_shutdown():
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(serve())
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
