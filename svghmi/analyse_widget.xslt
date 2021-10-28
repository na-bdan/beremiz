<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:exsl="http://exslt.org/common" xmlns:regexp="http://exslt.org/regular-expressions" xmlns:str="http://exslt.org/strings" xmlns:func="http://exslt.org/functions" xmlns:svg="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.0" extension-element-prefixes="ns func exsl regexp str dyn" exclude-result-prefixes="ns func exsl regexp str dyn svg inkscape">
  <xsl:output method="xml"/>
  <xsl:variable name="indexed_hmitree" select="/.."/>
  <xsl:variable name="pathregex" select="'^([^\[,]+)(\[[^\]]+\])?([\d,]*)$'"/>
  <xsl:template mode="parselabel" match="*">
    <xsl:variable name="label" select="@inkscape:label"/>
    <xsl:variable name="id" select="@id"/>
    <xsl:variable name="description" select="substring-after($label,'HMI:')"/>
    <xsl:variable name="_args" select="substring-before($description,'@')"/>
    <xsl:variable name="args">
      <xsl:choose>
        <xsl:when test="$_args">
          <xsl:value-of select="$_args"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$description"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="_type" select="substring-before($args,':')"/>
    <xsl:variable name="type">
      <xsl:choose>
        <xsl:when test="$_type">
          <xsl:value-of select="$_type"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$args"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:if test="$type">
      <widget>
        <xsl:attribute name="id">
          <xsl:value-of select="$id"/>
        </xsl:attribute>
        <xsl:attribute name="type">
          <xsl:value-of select="$type"/>
        </xsl:attribute>
        <xsl:for-each select="str:split(substring-after($args, ':'), ':')">
          <arg>
            <xsl:attribute name="value">
              <xsl:value-of select="."/>
            </xsl:attribute>
          </arg>
        </xsl:for-each>
        <xsl:variable name="paths" select="substring-after($description,'@')"/>
        <xsl:for-each select="str:split($paths, '@')">
          <xsl:if test="string-length(.) &gt; 0">
            <path>
              <xsl:variable name="path_match" select="regexp:match(.,$pathregex)"/>
              <xsl:variable name="pathminmax" select="str:split($path_match[4],',')"/>
              <xsl:variable name="path" select="$path_match[2]"/>
              <xsl:variable name="path_accepts" select="$path_match[3]"/>
              <xsl:variable name="pathminmaxcount" select="count($pathminmax)"/>
              <xsl:attribute name="value">
                <xsl:value-of select="$path"/>
              </xsl:attribute>
              <xsl:if test="string-length($path_accepts)">
                <xsl:attribute name="accepts">
                  <xsl:value-of select="$path_accepts"/>
                </xsl:attribute>
              </xsl:if>
              <xsl:choose>
                <xsl:when test="$pathminmaxcount = 2">
                  <xsl:attribute name="min">
                    <xsl:value-of select="$pathminmax[1]"/>
                  </xsl:attribute>
                  <xsl:attribute name="max">
                    <xsl:value-of select="$pathminmax[2]"/>
                  </xsl:attribute>
                </xsl:when>
                <xsl:when test="$pathminmaxcount = 1 or $pathminmaxcount &gt; 2">
                  <xsl:message terminate="yes">
                    <xsl:text>Widget id:</xsl:text>
                    <xsl:value-of select="$id"/>
                    <xsl:text> label:</xsl:text>
                    <xsl:value-of select="$label"/>
                    <xsl:text> has wrong syntax of path section </xsl:text>
                    <xsl:value-of select="$pathminmax"/>
                  </xsl:message>
                </xsl:when>
              </xsl:choose>
              <xsl:if test="$indexed_hmitree">
                <xsl:choose>
                  <xsl:when test="regexp:test($path,'^\.[a-zA-Z0-9_]+$')">
                    <xsl:attribute name="type">
                      <xsl:text>PAGE_LOCAL</xsl:text>
                    </xsl:attribute>
                  </xsl:when>
                  <xsl:when test="regexp:test($path,'^[a-zA-Z0-9_]+$')">
                    <xsl:attribute name="type">
                      <xsl:text>HMI_LOCAL</xsl:text>
                    </xsl:attribute>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:variable name="item" select="$indexed_hmitree/*[@hmipath = $path]"/>
                    <xsl:variable name="pathtype" select="local-name($item)"/>
                    <xsl:if test="$pathminmaxcount = 3 and not($pathtype = 'HMI_INT' or $pathtype = 'HMI_REAL')">
                      <xsl:message terminate="yes">
                        <xsl:text>Widget id:</xsl:text>
                        <xsl:value-of select="$id"/>
                        <xsl:text> label:</xsl:text>
                        <xsl:value-of select="$label"/>
                        <xsl:text> path section </xsl:text>
                        <xsl:value-of select="$pathminmax"/>
                        <xsl:text> use min and max on non mumeric value</xsl:text>
                      </xsl:message>
                    </xsl:if>
                    <xsl:if test="count($item) = 1">
                      <xsl:attribute name="index">
                        <xsl:value-of select="$item/@index"/>
                      </xsl:attribute>
                      <xsl:attribute name="type">
                        <xsl:value-of select="$pathtype"/>
                      </xsl:attribute>
                    </xsl:if>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:if>
            </path>
          </xsl:if>
        </xsl:for-each>
        <xsl:if test="svg:desc">
          <desc>
            <xsl:value-of select="svg:desc/text()"/>
          </desc>
        </xsl:if>
      </widget>
    </xsl:if>
  </xsl:template>
  <xsl:template mode="genlabel" match="arg">
    <xsl:text>:</xsl:text>
    <xsl:value-of select="@value"/>
  </xsl:template>
  <xsl:template mode="genlabel" match="path">
    <xsl:text>@</xsl:text>
    <xsl:value-of select="@value"/>
    <xsl:if test="string-length(@min)&gt;0 or string-length(@max)&gt;0">
      <xsl:text>,</xsl:text>
      <xsl:value-of select="@min"/>
      <xsl:text>,</xsl:text>
      <xsl:value-of select="@max"/>
    </xsl:if>
  </xsl:template>
  <xsl:template mode="genlabel" match="widget">
    <xsl:text>HMI:</xsl:text>
    <xsl:value-of select="@type"/>
    <xsl:apply-templates mode="genlabel" select="arg"/>
    <xsl:apply-templates mode="genlabel" select="path"/>
  </xsl:template>
  <xsl:variable name="hmi_elements" select="//svg:*[starts-with(@inkscape:label, 'HMI:')]"/>
  <xsl:template match="widget[@type='AnimateRotation']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>AnimateRotation - DEPRECATED, do not use.
</xsl:text>
      <xsl:text>Doesn't follow WYSIWYG principle, and forces user to add animateTransform tag in SVG (using inkscape XML editor for exemple)
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>AnimateRotation - DEPRECATED</xsl:text>
    </shortdesc>
    <path name="speed" accepts="HMI_INT,HMI_REAL">
      <xsl:text>speed</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='Back']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Back widget brings focus back to previous page in history when clicked.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Jump to previous page</xsl:text>
    </shortdesc>
  </xsl:template>
  <xsl:template match="widget[@type='Button']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Button widget takes one boolean variable path, and reflect current true
</xsl:text>
      <xsl:text>or false value by showing "active" or "inactive" labeled element
</xsl:text>
      <xsl:text>respectively. Pressing and releasing button changes variable to true and
</xsl:text>
      <xsl:text>false respectively. Potential inconsistency caused by quick consecutive
</xsl:text>
      <xsl:text>presses on the button is mitigated by using a state machine that wait for
</xsl:text>
      <xsl:text>previous state change to be reflected on variable before applying next one.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Push button reflecting consistently given boolean variable</xsl:text>
    </shortdesc>
    <path name="value" accepts="HMI_BOOL">
      <xsl:text>Boolean variable</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='CircularBar']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>CircularBar widget changes the end angle of a "path" labeled arc according
</xsl:text>
      <xsl:text>to value of the single accepted variable.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>If "min" a "max" labeled texts are provided, then they are used as
</xsl:text>
      <xsl:text>respective minimum and maximum value. Otherwise, value is expected to be
</xsl:text>
      <xsl:text>in between 0 and 100.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Change end angle of Inkscape's arc</xsl:text>
    </shortdesc>
    <arg name="min" count="optional" accepts="int,real">
      <xsl:text>minimum value</xsl:text>
    </arg>
    <arg name="max" count="optional" accepts="int,real">
      <xsl:text>maximum value</xsl:text>
    </arg>
    <path name="value" accepts="HMI_INT,HMI_REAL">
      <xsl:text>Value to display</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='CircularSlider']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>CircularSlider - DEPRECATED, to be replaced by PathSlider
</xsl:text>
      <xsl:text>This widget moves "handle" labeled group along "range" labeled
</xsl:text>
      <xsl:text>arc, according to value of the single accepted variable.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>If "min" a "max" labeled texts are provided, or if first and second
</xsl:text>
      <xsl:text>argument are given, then they are used as respective minimum and maximum
</xsl:text>
      <xsl:text>value. Otherwise, value is expected to be in between 0 and 100.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>If "value" labeled text is found, then its content is replaced by value.
</xsl:text>
      <xsl:text>During drag, "setpoint" labeled group is moved to position defined by user
</xsl:text>
      <xsl:text>while "handle" reflects current value from variable.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>CircularSlider - DEPRECATED</xsl:text>
    </shortdesc>
    <arg name="min" count="optional" accepts="int,real">
      <xsl:text>minimum value</xsl:text>
    </arg>
    <arg name="min" count="optional" accepts="int,real">
      <xsl:text>maximum value</xsl:text>
    </arg>
    <path name="value" accepts="HMI_INT,HMI_REAL">
      <xsl:text>Value to display</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='CustomHtml']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>CustomHtml widget allows insertion of HTML code in a svg:foreignObject.
</xsl:text>
      <xsl:text>Widget content is replaced by foreignObject. HTML code is obtained from
</xsl:text>
      <xsl:text>"code" labeled text content. HTML insert position and size is given with
</xsl:text>
      <xsl:text>"container" labeled element.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Custom HTML insert</xsl:text>
    </shortdesc>
  </xsl:template>
  <xsl:template match="widget[@type='Display']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>If Display widget is a svg:text element, then text content is replaced by
</xsl:text>
      <xsl:text>value of given variables, space separated.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Otherwise, if Display widget is a group containing a svg:text element
</xsl:text>
      <xsl:text>labelled "format", then text content is replaced by printf-like formated
</xsl:text>
      <xsl:text>string. In other words, if "format" labeled text is "%d %s %f", then 3
</xsl:text>
      <xsl:text>variables paths are expected : HMI_IN, HMI_STRING and HMI_REAL.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>In case Display widget is a svg::text element, it is also possible to give
</xsl:text>
      <xsl:text>format string as first argument.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Printf-like formated text display </xsl:text>
    </shortdesc>
    <arg name="format" count="optional" accepts="string">
      <xsl:text>printf-like format string when not given as svg:text</xsl:text>
    </arg>
    <path name="fields" count="many" accepts="HMI_INT,HMI_REAL,HMI_STRING,HMI_BOOL">
      <xsl:text>variables to be displayed</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='DropDown']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>DropDown widget let user select an entry in a list of texts, given as
</xsl:text>
      <xsl:text>arguments. Single variable path is index of selection.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>It needs "text" (svg:text or svg:use referring to svg:text),
</xsl:text>
      <xsl:text>"box" (svg:rect), "button" (svg:*), and "highlight" (svg:rect)
</xsl:text>
      <xsl:text>labeled elements.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>When user clicks on "button", "text" is duplicated to display enties in the
</xsl:text>
      <xsl:text>limit of available space in page, and "box" is extended to contain all
</xsl:text>
      <xsl:text>texts. "highlight" is moved over pre-selected entry.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>When only one argument is given and argment contains "#langs" then list of
</xsl:text>
      <xsl:text>texts is automatically set to the human-readable list of supported
</xsl:text>
      <xsl:text>languages by this HMI. 
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>If "text" labeled element is of type svg:use and refers to a svg:text 
</xsl:text>
      <xsl:text>element part of a TextList widget, no argument is expected. In that case
</xsl:text>
      <xsl:text>list of texts is set to TextList content.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Let user select text entry in a drop-down menu</xsl:text>
    </shortdesc>
    <arg name="entries" count="many" accepts="string">
      <xsl:text>drop-down menu entries</xsl:text>
    </arg>
    <path name="selection" accepts="HMI_INT">
      <xsl:text>selection index</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='ForEach']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>ForEach widget is used to span a small set of widget over a larger set of
</xsl:text>
      <xsl:text>repeated HMI_NODEs. 
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Idea is somewhat similar to relative page, but it all happens inside the
</xsl:text>
      <xsl:text>ForEach widget, no page involved.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Together with relative Jump widgets it can be used to build a menu to reach
</xsl:text>
      <xsl:text>relative pages covering many identical HMI_NODES siblings.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>ForEach widget takes a HMI_CLASS name as argument and a HMI_NODE path as
</xsl:text>
      <xsl:text>variable.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Direct sub-elements can be either groups of widget to be spanned, labeled
</xsl:text>
      <xsl:text>"ClassName:offset", or buttons to control the spanning, labeled
</xsl:text>
      <xsl:text>"ClassName:+/-number".
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>span widgets over a set of repeated HMI_NODEs</xsl:text>
    </shortdesc>
    <arg name="class_name" accepts="string">
      <xsl:text>HMI_CLASS name</xsl:text>
    </arg>
    <path name="root" accepts="HMI_NODE">
      <xsl:text> where to find HMI_NODEs whose HMI_CLASS is class_name</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='Input']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Input widget takes one variable path, and displays current value in
</xsl:text>
      <xsl:text>optional "value" labeled sub-element. 
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Click on optional "edit" labeled element opens keypad to edit value.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Operation on current value is performed when click on sub-elements with
</xsl:text>
      <xsl:text>label starting with '=', '+' or '-' sign. Value after sign is used as
</xsl:text>
      <xsl:text>operand.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Input field with predefined operation buttons</xsl:text>
    </shortdesc>
    <arg name="format" accepts="string">
      <xsl:text>optional printf-like format </xsl:text>
    </arg>
    <path name="edit" accepts="HMI_INT, HMI_REAL, HMI_STRING">
      <xsl:text>single variable to edit</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='JsonTable']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Send given variables as POST to http URL argument, spread returned JSON in
</xsl:text>
      <xsl:text>SVG sub-elements of "data" labeled element.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Documentation to be written. see svbghmi exemple.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Http POST variables, spread JSON back</xsl:text>
    </shortdesc>
    <arg name="url" accepts="string">
      <xsl:text> </xsl:text>
    </arg>
    <path name="edit" accepts="HMI_INT, HMI_REAL, HMI_STRING">
      <xsl:text>single variable to edit</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='Jump']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Jump widget brings focus to a different page. Mandatory single argument
</xsl:text>
      <xsl:text>gives name of the page.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Optional single path is used as new reference when jumping to a relative
</xsl:text>
      <xsl:text>page, it must point to a HMI_NODE.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>"active"+"inactive" labeled elements can be provided and reflect current
</xsl:text>
      <xsl:text>page being shown.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>"disabled" labeled element, if provided, is shown instead of "active" or
</xsl:text>
      <xsl:text>"inactive" widget when pointed HMI_NODE is null.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Jump to given page</xsl:text>
    </shortdesc>
    <arg name="page" accepts="string">
      <xsl:text>name of page to jump to</xsl:text>
    </arg>
    <path name="reference" count="optional" accepts="HMI_NODE">
      <xsl:text>reference for relative jump</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='Keypad']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Keypad - to be written
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Keypad </xsl:text>
    </shortdesc>
    <arg name="supported_types" accepts="string">
      <xsl:text>keypad can input those types </xsl:text>
    </arg>
  </xsl:template>
  <xsl:template match="widget[@type='List']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>List widget is a svg:group, list items are labeled elements
</xsl:text>
      <xsl:text>in that group.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>To use a List, clone (svg:use) one of the items inside the widget that
</xsl:text>
      <xsl:text>expects a List.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Positions of items are relative to each other, and they must all be in the
</xsl:text>
      <xsl:text>same place. In order to make editing easier it is therefore recommanded to
</xsl:text>
      <xsl:text>make stacked clones of svg elements spread nearby the list.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>A named list of named graphical elements</xsl:text>
    </shortdesc>
    <arg name="listname"/>
  </xsl:template>
  <xsl:template match="widget[@type='Meter']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Meter widget moves the end of "needle" labeled path along "range" labeled
</xsl:text>
      <xsl:text>path, according to value of the single accepted variable.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>Needle is reduced to a single segment. If "min" a "max" labeled texts
</xsl:text>
      <xsl:text>are provided, or if first and second argument are given, then they are used
</xsl:text>
      <xsl:text>as respective minimum and maximum value. Otherwise, value is expected to be
</xsl:text>
      <xsl:text>in between 0 and 100.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Moves "needle" along "range"</xsl:text>
    </shortdesc>
    <arg name="min" count="optional" accepts="int,real">
      <xsl:text>minimum value</xsl:text>
    </arg>
    <arg name="max" count="optional" accepts="int,real">
      <xsl:text>maximum value</xsl:text>
    </arg>
    <path name="value" accepts="HMI_INT,HMI_REAL">
      <xsl:text>Value to display</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='PathSlider']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>PathSlider - 
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Slide an SVG element along a path by dragging it</xsl:text>
    </shortdesc>
    <path name="value" accepts="HMI_INT,HMI_REAL">
      <xsl:text>value</xsl:text>
    </path>
    <path name="min" count="optional" accepts="HMI_INT,HMI_REAL">
      <xsl:text>min</xsl:text>
    </path>
    <path name="max" count="optional" accepts="HMI_INT,HMI_REAL">
      <xsl:text>max</xsl:text>
    </path>
    <arg name="min" count="optional" accepts="int,real">
      <xsl:text>minimum value</xsl:text>
    </arg>
    <arg name="max" count="optional" accepts="int,real">
      <xsl:text>maximum value</xsl:text>
    </arg>
  </xsl:template>
  <xsl:template match="widget[@type='ScrollBar']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>ScrollBar - svg:rect based scrollbar
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>ScrollBar</xsl:text>
    </shortdesc>
    <path name="value" accepts="HMI_INT">
      <xsl:text>value</xsl:text>
    </path>
    <path name="range" accepts="HMI_INT">
      <xsl:text>range</xsl:text>
    </path>
    <path name="visible" accepts="HMI_INT">
      <xsl:text>visible</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='Slider']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Slider - DEPRECATED - use ScrollBar or PathSlider instead
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Slider - DEPRECATED - use ScrollBar instead</xsl:text>
    </shortdesc>
    <path name="value" accepts="HMI_INT">
      <xsl:text>value</xsl:text>
    </path>
    <path name="range" accepts="HMI_INT">
      <xsl:text>range</xsl:text>
    </path>
    <path name="visible" accepts="HMI_INT">
      <xsl:text>visible</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='Switch']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Switch widget hides all subelements whose label do not match given
</xsl:text>
      <xsl:text>variable current value representation. For exemple if given variable type
</xsl:text>
      <xsl:text>is HMI_INT and value is 1, then elements with label '1' will be displayed.
</xsl:text>
      <xsl:text>Label can have comments, so '1#some comment' would also match. If matching
</xsl:text>
      <xsl:text>variable of type HMI_STRING, then double quotes must be used. For exemple,
</xsl:text>
      <xsl:text>'"hello"' or '"hello"#another comment' match HMI_STRING 'hello'.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Show elements whose label match value.</xsl:text>
    </shortdesc>
    <path name="value" accepts="HMI_INT,HMI_STRING">
      <xsl:text>value to compare to labels</xsl:text>
    </path>
  </xsl:template>
  <xsl:template match="widget[@type='TextList']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>TextList widget is a svg:group, list items are labeled elements
</xsl:text>
      <xsl:text>in that group.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>To use a TextList, clone (svg:use) one of the items inside the widget 
</xsl:text>
      <xsl:text>that expects a TextList.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>In this list, (translated) text content is what matters. Nevertheless
</xsl:text>
      <xsl:text>text style of the cloned item will be applied in client widget.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>A named list of ordered texts </xsl:text>
    </shortdesc>
    <arg name="listname"/>
  </xsl:template>
  <xsl:template match="widget[@type='TextStyleList']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>TextStyleList widget is a svg:group, list items are labeled elements
</xsl:text>
      <xsl:text>in that group.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>To use a TextStyleList, clone (svg:use) one of the items inside the widget 
</xsl:text>
      <xsl:text>that expects a TextStyleList.
</xsl:text>
      <xsl:text>
</xsl:text>
      <xsl:text>In this list, only style matters. Text content is ignored.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>A named list of named texts</xsl:text>
    </shortdesc>
    <arg name="listname"/>
  </xsl:template>
  <xsl:template match="widget[@type='ToggleButton']" mode="widget_desc">
    <type>
      <xsl:value-of select="@type"/>
    </type>
    <longdesc>
      <xsl:text>Button widget takes one boolean variable path, and reflect current true
</xsl:text>
      <xsl:text>or false value by showing "active" or "inactive" labeled element
</xsl:text>
      <xsl:text>respectively. Clicking or touching button toggles variable.
</xsl:text>
    </longdesc>
    <shortdesc>
      <xsl:text>Toggle button reflecting given boolean variable</xsl:text>
    </shortdesc>
    <path name="value" accepts="HMI_BOOL">
      <xsl:text>Boolean variable</xsl:text>
    </path>
  </xsl:template>
  <xsl:template mode="document" match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates mode="document" select="@* | node()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template mode="document" match="widget">
    <xsl:copy>
      <xsl:apply-templates mode="document" select="@* | node()"/>
      <defs>
        <xsl:apply-templates mode="widget_desc" select="."/>
      </defs>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/">
    <xsl:variable name="widgets">
      <xsl:apply-templates mode="parselabel" select="$hmi_elements"/>
    </xsl:variable>
    <xsl:variable name="widget_ns" select="exsl:node-set($widgets)"/>
    <widgets>
      <xsl:apply-templates mode="document" select="$widget_ns"/>
    </widgets>
  </xsl:template>
</xsl:stylesheet>
