from __future__ import annotations
from functools import reduce
from typing import Optional, Union

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL

from .requirement import Requirement

from .analyzer import Analyzer


class Ontoscen(Graph):
    """An RDF graph that respects the Ontoscen ontology.

    Class attributes:
        IRI (URIRef): identifier for the Ontoscen ontology.
    """

    ANALYZER = Analyzer()

    IRI: Namespace = Namespace(
        "http://sw.cientopolis.org/scenarios_ontology/0.1/scenarios.ttl#"
    )

    def __init__(self, requirements: Optional[list[Requirement]] = None):
        """Constructor for the Ontoscen class.

        Arguments:
            requirements (list[Requirement] - optional): list of
                requirements to be added.
        """
        super().__init__()

        self.parse("data/ontoscen.ttl", format="turtle", encoding="utf-8")

        if requirements:
            self.add_requirements(requirements)

    def add_requirements(self, requirements: list[Requirement]) -> Ontoscen:
        """Add a list of Requirements to the graph.

        Arguments:
            requirements (list[str]): scenarios to be added.
        """
        for requirement in requirements:
            self.add_requirement(requirement)
        return self

    def add_requirement(self, requirement: Requirement) -> Ontoscen:
        """Add a single Requirement to the graph.

        Arguments:
            requirement (str): scenario to be added.
        """
        # TODO: move most of this to Requirement or remove the class
        #   altogether
        scenario = self._add_scenario(requirement.scenario)
        self._add_goal(scenario, requirement.goal)
        self._add_context(scenario, requirement.context)
        for actor in requirement.actors:
            self._add_actor(scenario, actor)
        for resource in requirement.resources:
            self._add_resource(scenario, self.ANALYZER.lemmatize(resource))
        self._add_episodes(
            scenario,
            requirement.episodes,
            requirement.resources,
        )
        return self

    def count_individuals_of_type(self, a_type: str) -> int:
        """Count the amount of individuals belonging to a certain type

        Arguments:
            a_type (str): the RDF class whose individuals are to be
                counted.

        Returns:
            counter (int): amount of individuals of `a_type`.
        """
        return len(list(self.triples((None, RDF.type, self.IRI[a_type]))))

    def get_resources(self) -> list[URIRef]:
        """Retrieve the Resources on the Ontoscen graph

        Returns:
            resources (list[URIRef]): list of Resources.
        """
        return list(self.subjects(RDF.type, self.IRI["Resource"]))

    def get_actors(self) -> list[URIRef]:
        """Retrieve the Actors on the Ontoscen graph

        Returns:
            actors (list[URIRef]): list of Actors.
        """
        return list(self.subjects(RDF.type, self.IRI["Actor"]))

    def get_label(self, subject: URIRef) -> Union[Literal, None]:
        return next(self.objects(subject, RDFS.label), None)

    def _exists_individual_with(self, a_type: str, label: str) -> bool:
        """Check in the graph for an individual of type `a+type` and
        label `label`.

        Arguments:
            a_type (str): an RDF class.
            label (str): a description of the individual.

        Returns:
            exists (bool): is there such an individual in Ontoscen?
        """
        return (None, RDF.type, self.IRI[a_type]) in self and (
            None,
            RDFS.label,
            Literal(label),
        ) in self

    def get_individual(self, label: str) -> URIRef | bool:
        """Retrieve the individual of RDFS.label
            `label` or False if not found

        Arguments:
            label (str): a description of the individual.

        Returns:
            individual (URIRef): an subject linked with RDFS.label `label`.

        """
        return next(self.subjects(RDFS.label, Literal(label)), False)

    def is_linked(self, individual: URIRef) -> bool:
        """Check if an individual is linked with `OWL.sameAs` to any
        other individual.

        Arguments:
            individual (URIRef): the individual to be checked.

        Returns:
            linked (bool): is the individual linked?
        """

        return (individual, OWL.sameAs, None) in self or (
            None,
            OWL.sameAs,
            individual,
        ) in self

    def _add_scenario(self, scenario: str) -> URIRef:
        return self._add_individual("Scenario", scenario)

    def _add_condition(self, condition: str) -> URIRef:
        return self._add_individual("Condition", condition)

    def _add_goal(self, scenario: URIRef, goal: str) -> URIRef:
        individual: URIRef = self._add_condition(goal)
        self.add((scenario, self.IRI["hasGoal"], individual))
        return individual

    def _add_context(self, scenario: URIRef, context: str) -> URIRef:
        individual: URIRef = self._add_condition(context)
        self.add((scenario, self.IRI["hasContext"], individual))
        return individual

    def _add_actor(self, scenario: URIRef, actor: str) -> URIRef:
        individual: URIRef = self._add_individual(
            "Actor", self.ANALYZER.lemmatize(actor)
        )
        self.add((scenario, self.IRI["hasActor"], individual))
        return individual

    def _add_resource(self, scenario: URIRef, resource: str) -> URIRef:
        individual: URIRef = self._add_individual("Resource", resource)
        self.add((scenario, self.IRI["hasResource"], individual))
        return individual

    def _add_episodes(
        self, scenario: URIRef, episodes: list[str], resources
    ) -> None:
        reduce(
            self._add_dependency,
            map(
                lambda ep: self._add_episode(scenario, ep, resources),
                episodes,
            ),
            scenario,
        )

    def _add_action(self, episode, action):
        individual: URIRef = self._add_individual("Action", action)
        self.add((episode, self.IRI["hasAction"], individual))
        return individual

    def _add_dependency(self, required: URIRef, dependent: URIRef) -> URIRef:
        self.add((dependent, self.IRI["dependsOn"], required))
        self.add((required, self.IRI["requiredBy"], dependent))
        return dependent

    def _add_episode(
        self, scenario: URIRef, episode: str, resources
    ) -> URIRef:
        individual: URIRef = self._add_individual("Episode", episode)
        self.add((scenario, self.IRI["hasEpisode"], individual))
        self._analyze_episode(scenario, episode, individual, resources)
        return individual

    def _analyze_episode_for_actors(
        self, episode: str, episode_individual: URIRef
    ):
        actor = self.ANALYZER.analyze_for_actors(episode)

        if not actor:
            # the episode doesn't reference any actor...
            return
        if self._exists_individual_with("Resource", actor):
            # if actor exists in the graph as Resource, then append it to scenario with role "Actor"
            # TODO: inconsistency detected here
            self._add_actor(episode_individual, actor)
        else:
            # actor not already exists, or actor is an Actor
            self._add_actor(episode_individual, actor)

    def _analyze_episode_for_actions(
        self, episode: str, episode_individual: URIRef
    ):
        action = self.ANALYZER.analyze_for_actions(episode)
        if action:
            self._add_action(episode_individual, action)

    def _analyze_episode_for_resources(
        self,
        scenario: URIRef,
        episode: str,
        episode_individual: URIRef,
        resources: list[str],
    ):
        for resource in self.ANALYZER.analyze_for_resources(
            episode, scenario, resources
        ):
            if self._exists_individual_with("Actor", resource):
                # if resource exists in the graph as Actor, then append it to scenario with role "Resource"
                # TODO: inconsistency detected here

                self._add_resource(episode_individual, resource)
            else:
                # resource not already exists, or resource is a Resource
                self._add_resource(episode_individual, resource)
            resources.append(resource)

    def _analyze_episode(
        self,
        scenario: URIRef,
        episode: str,
        episode_individual: URIRef,
        resources: list[str],
    ):
        self._analyze_episode_for_actors(episode, episode_individual)
        self._analyze_episode_for_actions(episode, episode_individual)
        self._analyze_episode_for_resources(
            scenario, episode, episode_individual, resources
        )

    def _add_individual(self, a_type: str, label: str) -> URIRef:
        """Add an individual to Ontoscen if it doesn't exist.

        If the individual doesn't exist:
            Add it to Ontoscen.
        If the individual already exists:
            Return it.

        Arguments:
            a_type (str): the RDF class whose individuals are to be
                counted.

        Returns:
            individual (URIRef): a node with triples defining its class
                and label.
        """
        ind = self.get_individual(label)
        if type(ind) is URIRef:
            return ind

        individual: URIRef = self.IRI[
            a_type.lower() + str(self.count_individuals_of_type(a_type))
        ]

        self._add_type(individual, a_type)
        self._add_label(individual, label)

        return individual

    def _individual_exists(self, label):
        """Check if an individual with the recieved label exists in the
        Ontoscen graph.

        Arguments:
            label (str): the label of the individual to be checked.

        Returns:
            exists (bool): does the individual exist?
        """

        return (
            None,
            RDFS.label,
            Literal(label),
        ) in self

    def _add_label(self, individual, label):
        self.add((individual, RDFS.label, Literal(label)))

    def _add_type(self, individual, a_type):
        self.add((individual, RDF.type, self.IRI[a_type]))
