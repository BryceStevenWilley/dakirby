# Notes on HotDoc interview structure

Notes so far are just about the output of the interviews, haven't done a lot of interview parsing from hotdocs by itself yet.

HotDocs has a lot more files than [A2J interviews](a2j_structure.md).
There's `*.cmp`, `*.hpt`, `*.hpt.dll`, `*.hpt.js`, `*.hpt.manifest.xml`, and `*.hvc` (not always an `*.hvc`) for each of output docs in an interview.
For example, for a Child support interview there's one for each of these:
* `Coversheet`
* `FOC 10Dd Uniform Child Support Order Deviation Addendum`
* `FOC 10 Uniform Child Support Order`
* `FOC 10 Uniform Child Support Order Addendum`
* `FOC 50 Motion Regarding Support`
* `FOC 50 Motion Regarding Support Addendum`
* `Instructions`


## master cmp

Lots more preferences, can't tell a lot of them.

Seems like for all of the output vars, all of the actual questions asked
show up in this master cmp. You might have to look in [other *.cmp](#cmp) files
to find which one is the master.

The most important part of the master component file are the components.

## Components:

[3 types of components](https://help.hotdocs.com/preview/help/Components_Overview.htm#MiniTOCBookMark2):

* variable (if there's an A2J interview, usually duplicated): a field in docassemble. What actually gets the data from a user
* dialog: lets you group other components together in an interview (a DA screen?)
  * dialogs can be regular (None), or repeated (Series or Spreadsheet)
* computation: lets you calculate stuff (definitely a code block in DA)

Lots of information: https://help.hotdocs.com/preview/help/Components_Overview.htm#MiniTOCBookMark10


## Variables

Variables can be;
* multipleChoice
  * has options that can have separate prompts (in the variable)
* text
* date
* trueFalse
* number
* none (? on things like Introduction text and Dividers, so ignore)

Can also have `fieldWidth`, that can specify an exact width or a "calculated" width? idk why

Examples:

```
<hd:trueFalse name="Agree no PII TF" yesNoOnSameLine="true" askAutomatically="false">
	<hd:prompt>Do you understand that you should not enter any personal identifying information unless this tool specifically asks for it?</hd:prompt>
</hd:trueFalse>
```

```
<hd:text name="Defendant name first TE" askAutomatically="false" warnIfUnanswered="false">
	<hd:prompt>First</hd:prompt>
</hd:text>
```

```
<hd:multipleChoice name="Spouse in armed forces MC" askAutomatically="false" warnIfUnanswered="false">
	<hd:prompt>Is «Your spouse/the defendant CO» currently in the United States armed forces?</hd:prompt>
	<hd:fieldWidth widthType="exact" exactWidth="64"/>
	<hd:options>
		<hd:option name="Yes"/>
		<hd:option name="No"/>
		<hd:option name="I don&apos;t know"/>
	</hd:options>
```

`<singleSelection style="dropDownList"/>` for DA dropdowns.

Prompts can reference computations, i.e. Mako in labels or subquestions.

* `askAutomatically` is always false in the example interviews I have. I guess it's similar to `mandatory: True` in DA, but the ordering is probably different.
* `yesNoOnSameLine` is always true where it shows up, and it seems to show up on every `trueFalse` component except two (`Contains defendant marital kids TF` ash `Contains plaintiff marital kids TF`) are set by script.

## Dialogs

* Example: first screen of the Divorce tool:

```xml
<hd:dialogElement name="Divorce intro text 1">
  <hd:caption>«.b»Welcome to Michigan Legal Help&apos;s Do-It-Yourself Divorce tool.«.be»

Use this tool to draft forms to file for divorce in Michigan. This tool will ask you questions to make sure these forms are right for you, and it will use your answers to fill out the forms. After you complete the tool, your finished forms will be ready to download or print.

This tool may not be able to help you with every aspect of your divorce. In some cases, you may want to have a lawyer help you finish the divorce process. Use the «.w &quot;https://michiganlegalhelp.org/guide-to-legal-help&quot;»Guide to Legal Help«.we» to look for a lawyer or legal services near you. If you need a lawyer and are low-income, you may qualify for free legal help.
  </hd:caption>
</hd:dialogElement>
...
		<hd:dialogElement name="Horizontal Divider 1">
			<hd:horizontalDivider caption="«.lb»"/>
		</hd:dialogElement>
...
		<hd:dialogElement name="Click next">
			<hd:caption>Click the «.b»Next«.be» button below to continue.</hd:caption>
		</hd:dialogElement>
...
<hd:dialog name="Divorce Introduction Part 1">
	<hd:title>Introduction, Part 1</hd:title>
	<hd:contents>
		<hd:item name="Divorce intro text 1"/>
		<hd:item name="Horizontal Divider 1"/>
		<hd:item name="Click next"/>
	</hd:contents>
</hd:dialog>
```

Each dialog has a:
* name
* title
* content list
* a script
  * Scripts in dialogs look like they're run every turn, and do the show if logic. Not that there's a difference between something being answered as false, and something not being answered
    * example:
    ```
HIDE ALL
REQUIRE ALL

SHOW Introduction PII text
SHOW Agree no PII TF
IF Agree no PII TF
	SHOW Horizontal Divider 1
	SHOW Click next to continue
ELSE
	SHOW PII kickout
	SHOW Horizontal Divider 1
	SHOW Click X
END IF
    ```
* a style
* resource
* `linkVariables` attribute

I'm guessing that the `b` and `be` is bold and bold end, and `w` is "web", but just a link.

### Computations

Computations def need their own grammar / lexer / parser. can set arbitrary vars. RESULT is the value returned.
* SET x TO "y";
* IF X = "Y";
* ELSE IF X = "Y";
* ELSE
* END IF
* « and » substitutes vars, also «.lb» a lot.
* ANSWERED function
* // is comment

Have component identity properties:

* `name`: XML attribute
* `resultType`: XML attribute, either `text`, `number`, `date`, `true/false`, `none`
  * (not sure what none does. Can var mutation be global?)
* `parameters`: `<hd:parameters>`, and `<hd:parameter name="X" type="number"/>`

* sometimes there are `localVariables`?
* `script`: [Hotdocs script parser](https://help.hotdocs.com/preview/help/HotDocs_Scripting_Language_Overview.htm)?
* [Behaviors in scripts](https://help.hotdocs.com/preview/help/Computation_Editor.htm#Behavior_tab) let you change the default format for fields, default for unanswered text, and lets you set padding. Would have to come up with DA functions for that to work.
* notes: just comments

lol, it takes 52 lines of code just to set `plaintiffs = users` and `defendants = other_parties`

Computations, like docassemble, drive the interview order. There's a script that does everything, here's the first parts as an example.

```
Set language EN CO

DEFAULT Print divorce TF TO FALSE
DEFAULT Divorce interview complete TF TO FALSE
DEFAULT Home state is Michigan flag TF TO TRUE
...

SET Ask rest of interview 1 TF TO FALSE
...
DEFAULT Exit now 1 TF TO FALSE
...
SET Sec1Nr TO 1
...

ASK NONE
IF Divorce interview complete TF
	SET Print divorce TF TO TRUE
END IF

// = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
// = = = = = = = = = = = = = = = Begin Section 1  = = = = = = = = = = = = = = =
// = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
ASK Divorce Introduction Part 1
ASK Divorce Introduction Part 2
ASK Introduction PII
IF Agree no PII TF
	ASK Qualification part 1
	IF (Spouse in armed forces MC = &quot;No&quot; 
		OR (Spouse in armed forces MC = &quot;Yes&quot; AND Filing consent judgment of divorce MC = &quot;Yes&quot;))
		AND !Pending case TF AND Irreconcilable differences TF AND !Spouse is incompetent TF

		ASK Qualification part 2
		IF Ask rest of interview 1 TF
      ...
		ELSE
			SET Print divorce TF TO FALSE
		END IF
	ELSE
		SET Print divorce TF TO FALSE
	END IF
	// = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
	// = = = = = = = = = = = = = = = End of Section 1 = = = = = = = = = = = = = = =
	// = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


	// = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
	// = = = = = = = = = = = = = = = Begin Section 2  = = = = = = = = = = = = = = =
	// = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
	IF Continue from section 1 TF
		IF !With children CO
			// Section 2 is just for information regading children, so skip it if this
			// is a divorce without children.
			SET Continue from section 2 TF TO TRUE
			SET Sec3Nr TO 2
		ELSE
```

* `ASK` actually shows the dialog

## cmp

Component file: https://help.hotdocs.com/preview/help/Component_File_Overview.htm

http://www.hotdocs.com/schemas/component_library/2009

preferences:
* `TEMPLATE_ID`
* `TEMPLATE TITLE`: should be attachment title
* `TEMPLATE DESCRIPTION`: ? description in ALDoc?

and components. 

I don't get anything from this. TODO(brycew): revisit

#### hpt manifest xml

The Schema docs on template manifest: `xmlns="http://www.hotdocs.com/schemas/template_manifest/2012"`

Has a:
* templateID,
* hotdocsVersion,
* fileName (Instructions.hpt)
* effectiveCmpFile (Child Support Master.cmp)
* title
* then all of the variables (TBH, looks the same as what's in A2J, except type is spelled out. Types can be:
  * multipleChoice
  * text
  * date
  * trueFalse
  * number
  * none (? on things like Introduction text and Dividers, so ignore)
  * 
* dependencies
  * Instructions.cmp (the `baseCmpFile`)
  * Child Support Master.cmp (`pointedToCmpFile`)
  * png images (`interviewImage`: should make object blocks with DAStaticImages for those)
* 


All in all, this is good. But it would save me a bunch of time if I could build off of Johnathan's version. Waiting on a slack DM for that.

#### hvc

Just the variables? each with name, encodedName, and answerType. Not sure how it's
different than manifest yet. #todo  compare the two

#### hpt.js

Passes `HOTDOC$` through as `$`, has an `Ask` function. The rest of it does not make much sense. Looks like it repeats from other parts, like the master cmp or the manifest.

#### hpt.dll

Don't know how to look at it on Linux. Tried `wine ~/Downloads/depends.exe /c /of:output.txt Instructions.hpt.dll` with http://dependencywalker.com/, but it didn't seem to work:

```
Error: At least one module has an unresolved import due to a missing export function in an implicitly dependent module.
```

It might not be that important. With vim, at the end of the file, I can see `HotDocs Compiled Template`, `HotDocs Browser Interview`, `WrapNonExceptionThrows`, `_CorDllMain`, and `mscoree.dll`. 

#### hpt (the PDF layer)

It's compressed, so can't view it in vim. Ran `qpdf --stream-data=uncompress Instructions.hpt uncompressed-Instructions.pdf` to uncompress it. Instructions specifically didn't help much, a whole lot of translation matricies I think? Some ICC stuff near the end, and some font (?) stuff it looks like (a b c d e f near the beginning of sections.)

The FOC 50 was made by "DocuCom PDF Driver 9.00". Lots of matricies as normal, but at least we can see the text. At ~2125 we get (HotDocs Fields). Look like this:
```
219 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 276 0 R /P 156 0 R /Rect [ 48 528 57 537 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
220 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 277 0 R /P 156 0 R /Rect [ 96 528 105 537 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
221 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 278 0 R /P 156 0 R /Rect [ 148.9808 528 157.9808 537 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
222 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 279 0 R /P 156 0 R /Rect [ 48 504 57 513 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
223 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 280 0 R /P 156 0 R /Rect [ 48 480 57 489 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
224 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 281 0 R /P 156 0 R /Rect [ 48 420 57 429 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
225 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 282 0 R /P 156 0 R /Rect [ 320.7395 348.0449 329.7395 357.0449 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
226 0 obj
<< /Contents (HotDocs Field) /F 5 /HotDocsData 283 0 R /P 156 0 R /Rect [ 353.3415 589.1561 362.3415 598.1561 ] /Subtype /HotDocsInput /Type /Annot >>
endobj
...
```

HotDocsData seems to be the most relevant. The first number specifically, is the only thing that differs. Maybe it's all in JS?
