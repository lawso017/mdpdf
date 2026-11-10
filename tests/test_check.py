from mdpdf.check import find_problems


def page(words, width=612, height=792):
    body = "".join(
        f'<word xMin="{x0}" yMin="{y0}" xMax="{x1}" yMax="{y1}">{t}</word>'
        for x0, y0, x1, y1, t in words
    )
    return f'<page width="{width}" height="{height}">{body}</page>'


def doc(*pages):
    return "<html><body><doc>" + "".join(pages) + "</doc></body></html>"


def test_clean_page_has_no_problems():
    html = doc(page([(72, 100, 120, 110, "Hello"), (125, 100, 180, 110, "world")]))
    assert find_problems(html) == []


def test_word_past_the_right_margin_is_reported():
    html = doc(page([(500, 100, 600, 110, "uai-infra/terraform/modules/aws/ecs/main.tf")]))
    problems = find_problems(html)
    assert len(problems) == 1
    assert problems[0].page == 1 and problems[0].kind == "past margin"
    assert "uai-infra" in problems[0].text


def test_word_slightly_inside_the_margin_tolerance_is_fine():
    # 1in margin on Letter: text may end at 540; justified lines overshoot a little
    assert find_problems(doc(page([(480, 100, 543, 110, "fine")]))) == []


def test_overlapping_words_are_reported():
    html = doc(page([(100, 100, 200, 110, "/auth/internal/validate"), (180, 101, 260, 111, "silmaril-service")]))
    problems = find_problems(html)
    assert [p.kind for p in problems] == ["overlap"]
    assert "validate" in problems[0].text and "silmaril-service" in problems[0].text


def test_words_on_separate_lines_do_not_overlap():
    html = doc(page([(100, 100, 200, 110, "one"), (100, 112, 200, 122, "two")]))
    assert find_problems(html) == []


def test_rotated_page_skips_the_margin_check_but_keeps_overlaps():
    # a landscape (rotated) page reports coordinates beyond the portrait width
    words = [(700, 100, 760, 110, "wide"), (300, 300, 360, 310, "F3"), (330, 301, 390, 311, "F4")]
    problems = find_problems(doc(page(words)))
    assert [p.kind for p in problems] == ["overlap"]


def test_problems_carry_their_page_number():
    html = doc(page([(72, 100, 120, 110, "ok")]), page([(500, 100, 600, 110, "long")]))
    assert [p.page for p in find_problems(html)] == [2]


def test_adjacent_lines_with_tall_word_boxes_are_not_an_overlap():
    # pdftotext boxes include ascenders and descenders, so two lines 11.5pt apart with
    # 14.3pt boxes overlap by about 2.8pt without any ink touching (seen in diagram labels).
    html = doc(page([(104, 258.0, 133, 272.3, "Client"), (110, 269.6, 133, 283.9, "long")]))
    assert find_problems(html) == []
