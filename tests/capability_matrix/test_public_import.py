from semantic_facts import CapabilityMatrix, MatrixValidationError


def test_capability_matrix_public_imports() -> None:
    assert CapabilityMatrix is not None
    assert MatrixValidationError is not None

