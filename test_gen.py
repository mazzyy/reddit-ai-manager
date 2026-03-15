import sys
import asyncio
from backend.azure_ai import generate_content

def test():
    try:
        generate_content("test idea", ["test"])
        print("SUCCESS")
    except Exception as e:
        print(f"Exception type: {type(e)}")
        print(f"Exception str: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
