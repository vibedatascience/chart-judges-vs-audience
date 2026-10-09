"""Judge prompts, verbatim from the brief. Any edit is a new prompt version and must be logged in LOG.md."""

P1 = """You are judging the quality of a data visualization.
Rate this chart from 1 (very poor) to 10 (excellent), considering how clearly it communicates its data, how well it is designed, and how visually appealing it is.
Respond with JSON only: {"score": <integer 1-10>, "reason": "<one sentence>"}"""

P2 = """You are an expert in data visualization. Rate this chart on six dimensions, each from 1 (very poor) to 5 (excellent):
data_fidelity: the visual encoding represents the data accurately without distortion.
semantic_readability: a reader can easily understand what the chart shows.
insight_discovery: the chart helps a reader find meaningful patterns or insights.
design_style: the overall design is professional and consistent.
visual_composition: layout, spacing and hierarchy are well balanced.
color_harmony: colors are harmonious and support the message.
Respond with JSON only: {"data_fidelity": n, "semantic_readability": n, "insight_discovery": n, "design_style": n, "visual_composition": n, "color_harmony": n}"""

P3 = """Here are two data visualizations, Chart A and Chart B.
Which one is the better visualization overall, considering clarity, design quality and visual appeal?
Respond with JSON only: {"winner": "A" or "B", "confidence": <integer 1-5>, "reason": "<one sentence>"}"""

P3_AUDIENCE = """Both charts were posted to the Reddit community r/dataisbeautiful in the same week.
Which one do you think received more upvotes?
Respond with JSON only: {"winner": "A" or "B", "confidence": <integer 1-5>, "reason": "<one sentence>"}"""

TITLE_ONLY = """Two posts were made to r/dataisbeautiful in the same week. Which title got more upvotes? Answer A or B.
A: {title_a}
B: {title_b}"""

RETRY_SUFFIX = "\nRespond with valid JSON only."

PROMPTS = {"P1": P1, "P2": P2, "P3": P3, "P3-audience": P3_AUDIENCE, "title-only": TITLE_ONLY}
