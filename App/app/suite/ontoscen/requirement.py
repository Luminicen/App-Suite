class Requirement:
    """A Python representation of a software requirement specification
    in the form of scenarios.

    Attributes:
        scenario (str): The title of the scenario.
        goal (str): The objective to achieve with the scenario.
        context (str): The prerequisites of the scenario.
        actors (list[str]): The subjects that will do some activity to
            complete the scenario.
        resources (list[str]): The objects that will be used in the
            scenario.
        episodes (list[str]): The steps needed to complete the scenario.
    """

    def __init__(self, req: dict) -> None:
        """Initialize a Requirement object.

        Args:
            req (dict): A dictionary containing the requirement
                specification.
        """

        self.scenario: str = req["scenario"].lower()
        self.goal: str = req["goal"].lower()
        self.context: str = req["context"].lower()
        self.episodes: list[str] = list(
            map(lambda r: r.lower(), req["episodes"])
        )
        self.actors: list[str] = list(map(lambda r: r.lower(), req["actors"]))

        self.resources: list[str] = list(

            map(lambda r: r.lower(), req["resources"])

        )
