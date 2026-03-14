from mdpdf.naming import to_kebab


def test_spaces_to_kebab():
    assert to_kebab("My Document") == "my-document"


def test_underscores_to_kebab():
    assert to_kebab("org_chart") == "org-chart"


def test_camel_case_to_kebab():
    assert to_kebab("CamelCase") == "camel-case"


def test_mixed_separators():
    assert to_kebab("Mixed Case_with SPACES") == "mixed-case-with-spaces"


def test_already_kebab():
    assert to_kebab("already-kebab") == "already-kebab"


def test_consecutive_separators_collapsed():
    assert to_kebab("a--b__c  d") == "a-b-c-d"


def test_strips_leading_trailing_hyphens():
    assert to_kebab(" -foo- ") == "foo"
