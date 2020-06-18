import bokeh.models
from bokeh.models import ColumnDataSource
from bokeh.models.glyphs import Text
from bokeh.core.properties import value
from bokeh.models.tools import PolyDrawTool, PointDrawTool, ToolbarBox,FreehandDrawTool, ProxyToolbar, Toolbar
from bokeh.events import ButtonClick
from forest import wind, data

class BARC:
    barcTools = None
    def __init__(self, figures):
        self.figures = figures
        self.document = bokeh.plotting.curdoc()
        self.barcTools = bokeh.models.layouts.Column(name="barcTools")
        self.barctextstamp =[];
        self.windbarbs = []
        self.source_polyline = ColumnDataSource(data.EMPTY)
        for figure in self.figures:
            barc_tools = [
                self.polyLine(),
                #self.textStamp(figure),
                #self.windBarb(figure)
                ]
            #self.figure.tools = barc_tools
            figure.add_tools(*barc_tools)


    def polyLine(self):
        render_lines = []
        for figure in self.figures:
            render_lines.append(  figure.multi_line(
                xs="xs",
                ys="ys",
                source=self.source_polyline,
                alpha=0.3,
                color="red", level="overlay")
                )
        #text = Text(x="xs", y="ys", text=value("abc"), text_color="red", text_font_size="12pt")
        #render_line1 = figure.add_glyph(self.source_polyline,text)
        tool2 = FreehandDrawTool(
                    renderers=[render_lines[0]], 
                    tags=['barcfreehand'],
                    name="barcfreehand"
                    )
        self.source_polyline.js_on_change('data', 
            bokeh.models.CustomJS(args=dict(datasource = self.source_polyline, starting_font_size="30px", starting_colour="red", text=Text()), code="""
            console.log(datasource.data);
                """)
        )
        return tool2

    def textStamp(self, figure):
        self.source_text_stamp = ColumnDataSource(data.EMPTY)
        self.source_text_stamp.add([],"datasize")
        self.source_text_stamp.add([],"fontsize")
        self.source_text_stamp.add([],"colour")
        #render_text_stamp = self.figure.circle(x="xs",y="ys",legend_label="X", source=source);
        starting_font_size = 30 #in pixels 
        starting_colour = "orange" #in CSS-type spec 
        '''glyph = bokeh.models.Text(
                x="xs", 
                y="ys", 
                text=value("🌧"),  
                text_color="colour",
                text_font_size="fontsize")'''
        #glyph.text_font_size = '%spx' % starting_font_size

        #render_text_stamp = self.figure.add_glyph(self.source_text_stamp, glyph)
        render_text_stamp = figure.text_stamp(
                x="xs", 
                y="ys", 
                source=self.source_text_stamp,
                text=value("🌧"),  
                text_color="colour",
                text_font_size="fontsize"
                )
                
        self.source_text_stamp.js_on_change('data', 
            bokeh.models.CustomJS(args=dict(datasource = render_text_stamp.data_source, starting_font_size=starting_font_size, figure=figure, starting_colour=starting_colour), code="""
                for(var g = 0; g < datasource.data['fontsize'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = starting_colour;
                    }

                    if(!datasource.data['fontsize'][g])
                    {
                        datasource.data['fontsize'][g] = starting_font_size +'px';
                    }

                    //calculate initial datasize
                    if(!datasource.data['datasize'][g])
                    {
                        var starting_font_proportion = starting_font_size/(figure.inner_height);
                        datasource.data['datasize'][g] = (starting_font_proportion * (figure.y_range.end - figure.y_range.start));
                    }
                }
                """)
        )
        figure.y_range.js_on_change('start',
            bokeh.models.CustomJS(args=dict(render_text_stamp=render_text_stamp, glyph=render_text_stamp.glyph, figure=figure, starting_font_size=starting_font_size),code="""

            for(var g = 0; g < render_text_stamp.data_source.data['fontsize'].length; g++)
            {
                 render_text_stamp.data_source.data['fontsize'][g] = (((render_text_stamp.data_source.data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
            }
            glyph.change.emit();
            """)
        )
        #render_text_stamp = bokeh.models.renderers.GlyphRenderer(data_source=ColumnDataSource(dict(x=x, y=y, text="X")), glyph=bokeh.models.Text(x="xs", y="ys", text="text", angle=0.3, text_color="fuchsia"))
        tool3 = PointDrawTool(
                    renderers=[render_text_stamp],
                    tags= ['barctextstamp'],
                    )
        if len(self.barctextstamp) == 0:
            tool3.name = "MainBarcTextStamp"
        self.barctextstamp.append(tool3)
        return tool3

    def windBarb(self, figure):
        self.source_barb = ColumnDataSource(data.EMPTY)
        render_barb = figure.barb(
                x="xs", 
                y="ys", 
                u=-50,
                v=-50,
                source=self.source_barb
                )

        tool4 = PointDrawTool(
                    renderers=[render_barb],
                    custom_icon = 'forest/wind/barb.png',
                    tags= ['barcwindbarb']
                    )
        return tool4

    def ToolBar(self):
        toolbars = []
        for figure in self.figures:
            toolbars.append( figure.toolbar)
            self.barcTools.children.append(
                ToolbarBox(toolbar=figure.toolbar, toolbar_location="above")
            )
        #tools = sum([ toolbar.tools for toolbar in toolbars ], [])
        #tools.append(self.polyLine())
        freehandbutton = bokeh.models.widgets.Button(label="Freehand")
        freehands = list(self.barcTools.select({'tags': ['barcfreehand']}))
        freehandbutton.js_on_event(ButtonClick, bokeh.models.CustomJS(args=dict(freehands=freehands), code="""
            console.log("wibble");
            var each;
            for(each of freehands) { each.active = true; } 
            """))

        self.barcTools.children.append( freehandbutton)


        return self.barcTools
