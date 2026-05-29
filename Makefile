showm:
	uv run quarto preview --profile manuscript
showp:
	uv run quarto preview --profile presentation
presentation:
	uv run quarto render --profile presentation --to revealjs
manuscript:
	uv run quarto render --profile manuscript
