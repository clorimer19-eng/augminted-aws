import os
import time
import requests
from pathlib import Path

class TripoClient:
    BASE_URL = "https://api.tripo3d.ai/v2/openapi"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("TRIPO_API_KEY")
        if not self.api_key:
            raise ValueError("TRIPO_API_KEY is not set")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def upload_file(self, file_path: str) -> str:
        """Uploads a file and returns the image token."""
        url = f"{self.BASE_URL}/upload"
        file_path = Path(file_path)
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "image/jpeg")} # mime type might need adjustment
            response = requests.post(url, headers=self.headers, files=files)
            
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.text}")
            
        data = response.json()
        if data["code"] != 0:
             raise Exception(f"Upload API error: {data}")
             
        return data["data"]["image_token"]

    def create_task(self, image_token: str, file_type: str = "jpg") -> str:
        """Creates a text-to-model or image-to-model task."""
        url = f"{self.BASE_URL}/task"
        payload = {
            "type": "image_to_model",
            "file": {
                "type": "placeholder", # API docs usually say 'jpg' or similar, but let's check standard usage
                "file_token": image_token
            }
        }
        payload["file"]["type"] = file_type 

        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
             raise Exception(f"Create task failed: {response.text}")
             
        data = response.json()
        if data["code"] != 0:
             raise Exception(f"Create task API error: {data}")
             
        return data["data"]["task_id"]

    def get_task(self, task_id: str) -> dict:
        """Gets the task status."""
        url = f"{self.BASE_URL}/task/{task_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
             raise Exception(f"Get task failed: {response.text}")
             
        data = response.json()
        return data["data"]

    def poll_task(self, task_id: str, interval: int = 2, timeout: int = 300) -> str:
        """Polls until completion and returns the model URL."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            task = self.get_task(task_id)
            status = task["status"]
            
            if status == "success":
                # Depending on API version, output might be in 'output' or 'result'
                # V2: task['output']['model'] is the .glb url
                print(f"  [DEBUG] Task Success! Output: {task.get('output')}")
                if "model" in task["output"]:
                    return task["output"]["model"]
                elif "pbr_model" in task["output"]:
                     return task["output"]["pbr_model"]
                elif "base_model" in task["output"]:
                     return task["output"]["base_model"]
                else:
                     raise Exception(f"Unknown output format: {task['output']}")
            elif status == "failed":
                raise Exception(f"Task failed: {task}")
            elif status in ["cancelled", "unknown"]:
                 raise Exception(f"Task stopped with status: {status}")
            
            print(f"  ... task {task_id} is {status} (progress: {task.get('progress', 0)}%)")
            time.sleep(interval)
            
        raise TimeoutError("Task timed out")

    def download_model(self, url: str, save_path: str):
        """Downloads the model from the URL."""
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            raise Exception(f"Download failed: {response.status_code}")

# Helper function to run the full flow
def generate_glb_from_image(image_path: str, output_path: str, api_key: str = None):
    client = TripoClient(api_key)
    print(f"Uploading {image_path}...")
    token = client.upload_file(image_path)
    
    print(f"Creating task for token {token}...")
    file_ext = Path(image_path).suffix.lstrip(".").lower()
    if file_ext == "jpeg": file_ext = "jpg"
    task_id = client.create_task(token, file_type=file_ext)
    
    print(f"Polling task {task_id}...")
    model_url = client.poll_task(task_id)
    
    print(f"Downloading model to {output_path}...")
    client.download_model(model_url, output_path)
    print("Done.")

if __name__ == "__main__":
    # Test run
    import sys
    if len(sys.argv) > 2:
        generate_glb_from_image(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python tripo_client.py <input_image> <output_glb>")
