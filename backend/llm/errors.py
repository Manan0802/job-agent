class ModelUnavailable(ValueError):
    """The model could not produce a usable answer, after retries.

    Distinct from a bug in our own code: the request was fine, the model was
    busy, rate-limited, or spent its whole budget reasoning and returned
    nothing. Subclasses ValueError so callers that already handle a bad result
    keep working.
    """
