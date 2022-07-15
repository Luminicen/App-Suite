import spacy
from spacy.matcher import Matcher
from rdflib import URIRef

from collections import Counter

from .helpers import get_user_input

NLP = spacy.load("en_core_web_sm")

MATCHER = Matcher(NLP.vocab)


class Analyzer:
    def lemmatize(self, element: str):
        lemmatized_element = ""
        for token in NLP(element):
            if token.dep_ != "det":
                if token.pos_ != "VERB":
                    lemmatized_element += token.lemma_ + " "
                else:
                    lemmatized_element += token.text + " "

        return lemmatized_element.strip()

    def _getVerbPosition(self, sentence):
        pos = 0
        for token in sentence:
            relation = self._getRelation(sentence)
            if token.text == relation:
                return pos
            pos += 1

    def _getRelation(self, sentence):
        for token in sentence:
            if token.pos_ == "VERB":
                return token.text

    def _counter_of_matches(self, matches):
        return Counter(map(lambda match: match[0], matches))

    def _select_matches_from_candidates(
        self, match_id, matches, candidate_list
    ):
        # if it matches with match_id and it has more than one match is bc it is matching with the modifiers and without it
        # it should get the most complete match
        if self._counter_of_matches(matches)[NLP.vocab.strings[match_id]] > 1:
            return max(candidate_list, key=len)
        elif len(candidate_list) == 1:
            return candidate_list[0]

    def _get_actor(self, episode) -> str:
        episode = NLP(episode)

        matches = MATCHER(
            episode[0 : self._getVerbPosition(episode)], as_spans=True
        )

        return str(max(matches, key=len, default=""))

    def _remove_substrings(self, source, target):
        return list(
            filter(
                lambda s: not self.is_substring_of_any(s, target),
                source,
            )
        )

    def _remove_unnecessary_matches(
        self, candidate_resources, candidate_resources_of
    ):
        with_modifier = list(
            filter(lambda r: self._has_modifier(r), candidate_resources)
        )
        simples = list(
            filter(lambda r: r not in with_modifier, candidate_resources)
        )

        simples_that_matter = self._remove_substrings(simples, with_modifier)

        return self._analyze_of_match(candidate_resources_of) + list(
            filter(
                lambda r: not self.is_substring_of_any(
                    r, candidate_resources_of
                ),
                simples_that_matter + with_modifier,
            )
        )

    def _analyze_of_match(self, candidate_resources) -> list[str]:
        """
        If sentence matches with the "of" option:
        -> if [mod] [conj] [mod] [obj] ... then it's divided in two different resources, like [mod][obj]...
        -> if there's no [conj], it returns the [mod][obj]... match
        """
        if len(candidate_resources) > 0:
            candidate_resource = NLP(max(candidate_resources, key=len))
            for token in candidate_resource:
                if token.dep_ == "cc":
                    first_match = (
                        candidate_resource[0].text
                        + " "
                        + str(candidate_resource[3 : len(candidate_resource)])
                    )
                    second_match = str(
                        candidate_resource[2 : len(candidate_resource)]
                    )
                    return [first_match, second_match]
            return [" ".join(c.text for c in candidate_resource)]
        return []

    def _get_lemmatized_resources(self, episode):
        episode = NLP(episode)
        matches = MATCHER(episode)

        candidate_resources = set()
        candidate_resources_simple_dobj = list()
        candidate_resources_simple_pobj = list()
        candidate_resources_of = list()

        for match_id, start, end in matches:
            match = self.lemmatize(str(episode[start:end]))

            if NLP.vocab.strings[match_id] == "with":
                candidate_resources.add(match.replace("with", "").strip())
            elif NLP.vocab.strings[match_id] == "of":
                candidate_resources_of.append(match)
            elif NLP.vocab.strings[match_id] == "simple_dobj":
                candidate_resources_simple_dobj.append(match)
            elif NLP.vocab.strings[match_id] == "simple_pobj":
                candidate_resources_simple_pobj.append(match)

        candidate_resources = list(candidate_resources)
        candidate_resources += self._remove_unnecessary_matches(
            candidate_resources_simple_dobj, candidate_resources_of
        )

        # candidate_resources+=self._remove_substrings(candidate_resources_simple_pobj, candidate_resources)

        return candidate_resources

    def is_substring_of_any(self, simple, lista_compuestos):
        return any(simple in c for c in lista_compuestos)

    def _has_modifier(self, resource):
        return " " in resource

    def _add_rules_for_actors(self):
        MATCHER.add(
            "nominal_subject",
            [
                [
                    {"DEP": {"IN": ["compound", "amod"]}, "OP": "?"},
                    {
                        "POS": "NOUN",
                        "DEP": {
                            "IN": ["nsubj", "nsubjpass", "compound", "ROOT"]
                        },
                    },
                ],
            ],
        )

    def _remove_rules_for_actors(self):
        MATCHER.remove("nominal_subject")

    def _add_rules_for_resources(self):
        MATCHER.add(
            "with",
            [
                [
                    {"ORTH": "with"},  # with
                    {"DEP": "det", "OP": "?"},  # the
                    {"DEP": {"IN": ["amod", "compound"]}, "OP": "?"},  # tomato
                    {"DEP": {"IN": ["dobj", "pobj"]}},  # plant
                ],
            ],
        )
        MATCHER.add(
            "of",
            [
                [
                    {"POS": "ADJ", "OP": "?"},  # big
                    {"POS": "CCONJ", "OP": "?"},  # and
                    {"POS": "ADJ", "OP": "?"},  # great
                    {"DEP": "dobj"},  # results
                    {"ORTH": "of"},  # of
                    {"DEP": "det", "OP": "?"},  # the
                    {"DEP": {"IN": ["amod", "compound"]}, "OP": "?"},  # soil
                    {"DEP": {"IN": ["dobj", "pobj", "poss"]}},  # analysis
                ]
            ],
        )

        MATCHER.add(
            "simple_dobj",
            [
                [
                    {"DEP": {"IN": ["amod", "compound"]}, "OP": "?"},  # tomato
                    {"POS": "NOUN", "DEP": "dobj"},  # plant
                ]
            ],
        )

        MATCHER.add(
            "simple_pobj",
            [
                [
                    {"POS": "NOUN", "DEP": "pobj"},
                ]
            ],
        )

    def _remove_rules_for_resources(self):
        MATCHER.remove("of")
        MATCHER.remove("with")
        MATCHER.remove("simple_dobj")
        MATCHER.remove("simple_pobj")

    def _add_rules_for_actions(self):
        MATCHER.add(
            "verb",
            [
                [{"POS": "VERB", "DEP": "ROOT"}],
            ],
        )

        MATCHER.add(
            "tobe",
            [
                [
                    {"POS": "PART", "DEP": "aux"},
                    {"POS": "VERB", "DEP": "xcomp"},
                ],
            ],
        )

    def _remove_rules_for_actions(self):
        MATCHER.remove("verb")
        MATCHER.remove("tobe")

    def analyze_for_actors(self, episode) -> str:
        self._add_rules_for_actors()
        actor = self._get_actor(episode)
        self._remove_rules_for_actors()
        return actor

    def _get_resources(self, episode, resources):
        # this method is just necessary bc is needed to ask the user for adding some resources, and we don't want to ask twice
        # when delete it, modify analyze_for_resources to just add all resources found as in get_actor method
        # remove resources parameter too
        not_included = list()
        included = list()

        resources = [self.lemmatize(r) for r in resources]

        for resource in self._get_lemmatized_resources(episode):
            if resource not in resources:
                not_included.append(resource)
            else:
                included.append(resource)

        return not_included, included

    def _get_action(self, episode) -> str:
        episode = NLP(episode)

        matches = MATCHER(episode, as_spans=True)
        return " ".join([str(match) for match in matches])

    def analyze_for_actions(self, episode) -> str:
        self._add_rules_for_actions()
        accion = self._get_action(episode)

        self._remove_rules_for_actions()
        return accion

    def analyze_for_resources(
        self, episode: str, scenario: URIRef, resources: list[str]
    ) -> list[str]:
        self._add_rules_for_resources()
        not_included_resources, included_resources = self._get_resources(
            episode, resources
        )
        result = list()
        if len(not_included_resources) > 1:
            print(
                f"The following resources are not defined for scenario {scenario}."
                "Select the number/s of the resource/s you want to include, or press Enter to skip.",
                sep="\n",
            )

            for index, resource_not_included in enumerate(
                not_included_resources
            ):
                print(str(index + 1) + ")", resource_not_included)

            indexes = 'y' #get_user_input("Options: ").replace("\n", " ").split()

            if indexes == ["y"] or indexes == ["Y"]:
                result = not_included_resources
            else:
                for index in indexes:
                    if int(index) <= len(not_included_resources):
                        result.append(not_included_resources[int(index) - 1])

        elif len(not_included_resources) == 1:
            result.append(not_included_resources[0])

        self._remove_rules_for_resources()
        return result + included_resources
