import os
import argparse

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts import system_prompt
from call_function import (
    available_functions,
    call_function,
)

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"


def main():
    parser = argparse.ArgumentParser(description="Chatbot")

    parser.add_argument(
        "user_prompt",
        type=str,
        help="User prompt",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    messages: list[types.Content] = [
        types.Content(
            role="user",
            parts=[
                types.Part(text=args.user_prompt),
            ],
        )
    ]

    for _ in range(10):
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions],
                system_instruction=system_prompt,
                temperature=0,
            ),
        )

        if response.candidates:
            for candidate in response.candidates:
                messages.append(candidate.content)

        if response.function_calls:
            function_responses = []

            for function_call in response.function_calls:
                function_call_result = call_function(
                    function_call,
                    verbose=args.verbose,
                )

                if not function_call_result.parts:
                    raise RuntimeError(
                        "Function call result has no parts"
                    )

                function_response = (
                    function_call_result.parts[0]
                    .function_response
                )

                if function_response is None:
                    raise RuntimeError(
                        "Function response is missing"
                    )

                if function_response.response is None:
                    raise RuntimeError(
                        "Function response content is missing"
                    )

                function_responses.append(
                    function_call_result.parts[0]
                )

                if args.verbose:
                    print(
                        "-> "
                        f"{function_response.response}"
                    )

            messages.append(
                types.Content(
                    role="user",
                    parts=function_responses,
                )
            )

        else:
            print("Final response:")
            print(response.text)
            return

    print("Error: Agent reached max iterations without completion")


if __name__ == "__main__":
    main()