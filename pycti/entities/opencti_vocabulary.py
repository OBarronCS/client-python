import json


class Vocabulary:
    def __init__(self, opencti):
        self.opencti = opencti
        self.properties = """
            id
            name
            category {
                key
                fields {
                    key
                }
            }
        """

    def list(self, **kwargs):
        filters = kwargs.get("filters", None)
        self.opencti.log(
            "info", "Listing Vocabularies with filters " + json.dumps(filters) + "."
        )
        query = (
            """
                    query Vocabularies($filters: [VocabularyFiltering!]) {
                        vocabularies(filters: $filters) {
                            edges {
                                node {
                                    """
            + self.properties
            + """
                        }
                    }
                }
            }
        """
        )
        result = self.opencti.query(
            query,
            {
                "filters": filters,
            },
        )
        return self.opencti.process_multiple(result["data"]["vocabularies"])

    def read(self, **kwargs):
        id = kwargs.get("id", None)
        filters = kwargs.get("filters", None)
        if id is not None:
            self.opencti.log("info", "Reading vocabulary {" + id + "}.")
            query = (
                """
                        query Vocabulary($id: String!) {
                            vocabulary(id: $id) {
                                """
                + self.properties
                + """
                    }
                }
            """
            )
            result = self.opencti.query(query, {"id": id})
            return self.opencti.process_multiple_fields(result["data"]["vocabulary"])
        elif filters is not None:
            result = self.list(filters=filters)
            if len(result) > 0:
                return result[0]
            else:
                return None
        else:
            self.opencti.log(
                "error", "[opencti_vocabulary] Missing parameters: id or filters"
            )
            return None

    def handle_vocab(self, vocab, cache, field):
        if "vocab_" + vocab in cache:
            vocab_data = cache["vocab_" + vocab]
        else:
            vocab_data = self.read_or_create_unchecked(
                name=vocab,
                required=field["required"],
                category=cache["category_" + field["key"]],
            )
        if vocab_data is not None:
            cache["vocab_" + vocab] = vocab_data
        return vocab_data

    def create(self, **kwargs):
        name = kwargs.get("name", None)
        category = kwargs.get("category", None)

        if name is not None and category is not None:
            self.opencti.log(
                "info", "Creating or Getting aliased Vocabulary {" + name + "}."
            )
            query = (
                """
                        mutation VocabularyAdd($input: VocabularyAddInput!) {
                            vocabularyAdd(input: $input) {
                                """
                + self.properties
                + """
                    }
                }
            """
            )
            result = self.opencti.query(
                query,
                {
                    "input": {
                        "name": name,
                        "category": category,
                    }
                },
            )
            return result["data"]["vocabularyAdd"]
        else:
            self.opencti.log(
                "error",
                "[opencti_vocabulary] Missing parameters: name or category",
            )

    def read_or_create_unchecked(self, **kwargs):
        value = kwargs.get("name", None)
        vocab = self.read(filters=[{"key": "name", "values": [value]}])
        if vocab is None:
            try:
                return self.create(**kwargs)
            except ValueError:
                return None
        return vocab