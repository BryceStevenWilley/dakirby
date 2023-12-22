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

components are all of the variables. (also duplicated from A2J?), all selections and numbers and text there. Also computations.

Computations def need their own grammar / lexer / parser. can set arbitrary vars. RESULT is the value returned.
* SET x TO "y";
* IF X = "Y";
* ELSE IF X = "Y";
* ELSE
* END IF
* « and » substitutes vars, also «.lb» a lot.
* ANSWERED function
* // is comment

dialogElement, and dialog

lol, it takes 52 lines of code just to set `plaintiffs = users` and `defendants = other_parties`

## cmp

http://www.hotdocs.com/schemas/component_library/2009

preferences:
* `TEMPLATE_ID`
* `TEMPLATE TITLE`: should be attachment title
* `TEMPLATE DESCRIPTION`: ? description in ALDoc?

and components. 

I don't get anything from this. TODO(brycew): revisit

#### hpt manifest xml

[The Schema docs on template manifest](http://www.hotdocs.com/schemas/template_manifest/2012)

Has a:
* templateID,
* hotdocsVersion,
* fileName (Instructions.hpt)
* effectiveCmpFile (Child Support Master.cmp)
* title 
* then all of the variables (TBH, looks the same as what's in A2J, except type is spelled out (multipleChoice, text, date, trueFalse, number, etc.) Should check that.)
* dependencies
	* Instructions.cmp (the baseCmpFile)
	* Child Support Master.cmp (pointedToCmpFile))


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
