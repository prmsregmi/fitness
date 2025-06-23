"""Module for interacting with FutureHouse API and PaperQA library.

This module provides functions to interact with the FutureHouse API for AI-based
disease research and the PaperQA library for document analysis.
"""

import os
import time
import logging
import asyncio
from typing import Union, List, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def future_house_crow_api(query) -> Union[List[Any], Any]:
    """Interact with the FutureHouse API to query AI-developed disease treatments.

    Returns:
        Union[List[Any], Any]: Response from the FutureHouse API containing
        information about AI-developed treatments for neglected diseases.
    
    Raises:
        ImportError: If the futurehouse_client package is not installed.
    """
    try:
        from futurehouse_client import FutureHouseClient, JobNames
    except ImportError:
        logger.error("FutureHouseClient not found. Please install the futurehouse package.")
        return

    api_key = os.getenv('FUTURE_HOUSE_API_KEY')
    if not api_key:
        logger.error("FUTURE_HOUSE_API_KEY not found in environment variables")
        return

    client = FutureHouseClient(
        api_key=api_key,
    )

    task_data = {
        "name": JobNames.CROW,
        "query": query,
    }

    logger.info(f"Starting FutureHouse API request with query: {query}")

    return client.run_tasks_until_done(task_data)

def paper_qa_lib() -> Any:
    """Query the PaperQA library for information about PaperQA2.

    Returns:
        Any: Response from PaperQA containing information about PaperQA2.
    
    Raises:
        ImportError: If the paper-qa package is not installed.
    """
    try:
        from paperqa import Settings, ask
    except ImportError:
        logger.error("PaperQA not found. Please install with `uv pip install paper-qa`")
        return
    
    answer_response = ask(
        "What is PaperQA2?",
        settings=Settings(temperature=0.5, paper_directory="data/papers"),
    )
    return answer_response


if __name__ == "__main__":
    start = time.time()
    query = "Which neglected diseases had a treatment developed by artificial intelligence?"
    task_response = future_house_api(query)
    end = time.time()
    logger.info(f"Total time taken: {end - start:.2f} seconds")
    
    # Ensure the directory exists
    os.makedirs('data/response', exist_ok=True)
    file_path = 'data/response/task_response.txt'
    
    with open(file_path, 'w') as f:
        if isinstance(task_response, list):
            for idx, item in enumerate(task_response, 1):
                f.write(f"Item {idx}:\n")
                f.write(f"{item}\n\n")
        else:
            f.write(str(task_response))
    
    logger.info(f"Response saved to {file_path}")