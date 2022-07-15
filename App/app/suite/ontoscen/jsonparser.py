from json import load

from .requirement import Requirement


class JSONParser:
    """A class to retrieve requirements from a JSON file.

    The input file must be a list of JSON objects with the following
    structure:

        {
            "scenario": <str>,
            "goal": <str>,
            "context": <str>,
            "actors": <list[str]>,
            "resources": <list[str]>,
            "episodes": <list[str]>
        }
    """

    def __init__(self, file_name: str):
        """Initialize the JSONParser object."""
        with open(file_name, mode="r", encoding="utf8") as file:
            self.data: dict = load(file)

    def requirements(self) -> list[Requirement]:
        """Get a list of objects representing each parsed requirement.

        Returns:
            requirements (list[Requirement]): list of requirements.
        """
        return list(map(lambda req: Requirement(req), self.data))
