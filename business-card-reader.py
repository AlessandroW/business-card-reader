#!/usr/bin/env python3
"""Business Card Reader

- License: MIT
- Copyright: Dr. Alessandro Wollek <contact@wollek.ai>
"""
import argparse
from pathlib import Path
import subprocess
import base64
import io

from PIL import Image
import requests

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Business card reader")
    parser.add_argument(
        "--api-key", type=str, required=True, help="OpenAI API key for authentication"
    )
    parser.add_argument(
        "--file-path",
        type=str,
        required=True,
        help="Business card path to be processed",
    )

    args = parser.parse_args()

    api_key = args.api_key
    file_path = Path(args.file_path).absolute()

    if not file_path.exists():
        parser.error(f"The file path '{file_path}' does not exist.")
        exit(1)

    if not file_path.is_file():
        parser.error(f"The path '{file_path}' is not a file.")
        exit(1)

    if file_path.suffix.lower() == ".pdf":
        jpg_path = file_path.with_suffix(".jpg")
        if not jpg_path.exists():
            print(f"Converting '{file_path}' to '{jpg_path}'")
            try:
                subprocess.run(
                    ["magick", "convert", str(file_path), str(jpg_path)], check=True
                )
                print(f"Conversion successful: '{jpg_path}'")
            except subprocess.CalledProcessError as e:
                print(f"Error during conversion: {e}")
                exit(1)
        file_path = jpg_path

    buffered = io.BytesIO()

    with Image.open(file_path) as businesscard:
        businesscard.resize((512, 512)).save(buffered, format="jpeg")

    # Businesscard as Base64
    base64_card = base64.b64encode(buffered.getvalue()).decode("utf-8")

    prompt_messages = [
        {
            "role": "user",
            "content": [
                "This is a business card."
                "Extract all entities and label them. For example, first name, last name, company. ",
                "Return ONLY the result as a key-value list with the syntax:",
                "`- key :: value  `",
                "Example: ",
                "`- First Name :: Mike`",
                {"image": base64_card},
            ],
        },
    ]
    params = {
        "model": "gpt-4o-mini",
        "messages": prompt_messages,
        "max_tokens": 1000,
        "temperature": 0,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json=params,
        headers={"Authorization": f"Bearer {api_key}"},
    )

    if response.status_code != 200:
        print(response.text)
        exit(1)

    parsed_card = response.json()["choices"][0]["message"]["content"]
    print(parsed_card)
