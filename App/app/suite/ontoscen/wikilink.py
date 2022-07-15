from json import dump, load
from threading import Lock

from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDFS
from wikibase_api import Wikibase

from .helpers import get_user_input
from .ontoscen import Ontoscen


CACHE_FILE = "data/cache.json"

SCHEMA = Namespace("https://schema.org/")

WB = Wikibase()

IO_LOCK = Lock()


class Wikilink:
    """A class to link an Ontoscen graph with information from Wikidata.

    Attributes:
        LIMIT (int): max amount of items to choose from for each
            subject.
        MAX_WORKERS (int): max amount of threads to use.
        CACHE (dict): a cache of Wikidata search results.
    """

    def __init__(self, limit: int = 10, max_workers: int = 10):
        """Initialize a Wikilink object.

        Arguments:
            limit (int): max amount of items to choose from for each
                subject.
            max_workers (int): max amount of threads to use.
        """
        self.LIMIT: int = limit
        self.MAX_WORKERS = max_workers
        self.CACHE: dict = self.open_cache()

    def enrich(self, graph: Ontoscen) -> Ontoscen:
        """Enrich the resources and actors of an Ontoscen graph with
        Wikidata.

        Arguments:
            graph (Ontoscen): an Ontoscen graph.

        Returns:
            graph (Ontoscen): an Ontoscen graph linked with Wikidata.
        """

        from concurrent.futures import ThreadPoolExecutor, as_completed

        result = Ontoscen()

        try:
            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                futures = [
                    executor.submit(self._enrich_subject, graph, subject)
                    for subject in set(
                        graph.get_resources() + graph.get_actors()
                    )
                ]

                for future in as_completed(futures):
                    result += future.result()
        finally:
            self.save_cache()

        return result

    def open_cache(self) -> dict:
        """Open the cache file and return the contents.

        Returns:
            cache (dict): a cache of Wikidata search results.
        """

        try:
            with open(CACHE_FILE, mode="r", encoding="utf-8") as file:
                return load(file)
        except FileNotFoundError:
            return {}

    def save_cache(self) -> None:
        """Save the cache to a file."""

        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            dump(self.CACHE, file, ensure_ascii=False, indent=4)

    def _enrich_subject(self, ontoscen: Ontoscen, subject: URIRef) -> Ontoscen:
        """Enrich a subject with Wikidata information.

        Arguments:
            ontoscen (Ontoscen): an Ontoscen graph.
            subject (URIRef): a subject to enrich.

        Returns:
            ontoscen (Ontoscen): an Ontoscen graph with a subject linked
                with Wikidata.
        """

        if ontoscen.is_linked(subject):
            return ontoscen

        label = ontoscen.get_label(subject)
        if not label:
            return ontoscen

        results: list = self._query(label.toPython())

        if not results:
            return ontoscen

        with IO_LOCK:
            chosen_result: dict = self._take_input(results, subject, label)

        if not chosen_result:
            return ontoscen

        ontoscen.add(
            (subject, OWL.sameAs, URIRef(chosen_result["concepturi"]))
        )
        ontoscen.add((subject, RDFS.label, Literal(chosen_result["label"])))

        if "description" in chosen_result:
            ontoscen.add(
                (
                    subject,
                    SCHEMA.description,
                    Literal(chosen_result["description"]),
                )
            )

        return ontoscen

    def _take_input(
        self, options: list[dict], subject: URIRef, subject_label: Literal
    ) -> dict:
        """Take input from the user to choose a Wikidata item.

        Arguments:
            options (list[dict]): a list of Wikidata search results.
            subject (URIRef): a subject to enrich.
            subject_label (Literal): the subject's label.

        Returns:
            chosen_result (dict): a Wikidata search result.
        """
        print(
            "--------------------------------------------------------------------------------------------------------------------",
            f"The subject '{subject_label}' ({subject}) matches the following wikidata concepts.",
            "Select the most suitable option, or press Enter to skip.",
            "",
            sep="\n",
        )

        index: int = 0
        for option in options:
            index += 1
            item: str = option["concepturi"]
            label: str = option["label"]

            description: str = ""
            if "description" in option:
                description: str = option["description"]

            print(
                f"{index}) {label}:",
                f"ConceptUri: {item}",
                sep="\n",
            )

            if description:
                print(f"Description: {description}")

            print("")

        selection = 1 #get_user_input("Select: ")
        try:
            return options[int(selection) - 1]
        except:
            return {}

    def _is_in_cache(self, item_label: str) -> bool:
        """Check if a Wikidata item is in the cache taking the amount of
        results and the limit into account.

        Arguments:
            item_label (str): a Wikidata item label.

        Returns:
            is_in_cache (bool): is the item present in the cache? Is the
                amount of results enough?
        """

        return (item_label in self.CACHE) and (
            self.CACHE[item_label]["limit"]
            > len(self.CACHE[item_label]["results"])
            or len(self.CACHE[item_label]["results"]) >= self.LIMIT
        )

    def _query(self, item_label: str) -> list[dict]:
        """Query Wikidata for a given item label.
        Save the results in the cache if it's not already there.

        Arguments:
            item_label (str): a Wikidata item label.

        Returns:
            results (list[dict]): a list of Wikidata search results.
        """

        if not self._is_in_cache(item_label):
            self.CACHE[item_label] = {
                "limit": self.LIMIT,
                "results": WB.entity.search(
                    item_label, "en", limit=self.LIMIT
                )["search"],
            }

        return self.CACHE[item_label]["results"][: self.LIMIT]
