# Notes about A2J interview structure

Always check the [A2J Author](https://www.a2jauthor.org/content/a2j-authoring-guide) for more info.

A2J files include:

* any images that are used in the interview (should be JPGs)
* a `Guide.xml`, and
* a `Guide.json`

The Guide files seem to be identical, besides from the formats. I've decided to parse the XML format, and it's a bit more readable than the JSON without as much semantic information or names.

## The Guide.xml

Info = roughly metadata
* Authors - Authors
* Toolversion (should save as A2J version in DA)
* ignore Avatar, guide gender, avatarskintone, avatarhaircolor
* description
* email contact (?) It's Ang's email, so maybe just the standard author email in `setup.py?`
* jurisdiction
* title == title
* first page: 1-introduction

Then `PAGES`
* TEXT is for sure subquestion. Can make the first sentence the question, maybe.
	* if first paragraph tag is < 15 words, make question that, otherwise use PAGE Name striped of first number
	* Should be able to do HTML-to-markdown in the TEXT to get back to normal docassemble subquestion. Could do that later though. Can at least change em and strong, that's easy.
* LEARN: should eventually become a template subject, and HELP should be the contents. That's not a bad default.
* HELP can become help I guess.
* HELPIMAGE, should save the image name in a DAStaticImage object, and show it on the image screen.
* FIELDS: each FIELD has type (numberdollar), REQUIRED, NAME, and INVALID PROMPT
* BUTTONS: can make a whole graph of the interview with BUTTONS. Should then try to turn the graph into a mandatory code block.
	* BUTTONS also set the values of the variables in them BUTTON / NAME, VALUE

NOTE (don't know what to do if it's nested=true).

Then `STEPS`
Just the same as sections. Need the numbers for mapping things, but not a fan of them. Make the section names normal.

Then `VARIABLES`
* NAME
* TYPE:
	* TF = True False (probably yesnoradio)
	* MC = multiple choice (choices)
	* Text = string (normal DA field entry)
	* Number = float, unclear if currency or int or float
	* Date = date
* REPEATING = if present, def a list. If multiple vars have some shared prefix (first word maybe?), then make them part of the same ALIndividual object
* COMMENT = preserve as a comment in the question maybe?


## Misc links to the A2J Author docs

* https://www.a2jauthor.org/content/appendix-c-variable-naming-conventions
* https://www.a2jauthor.org/content/new-page
* https://www.a2jauthor.org/content/advanced-logic-section

