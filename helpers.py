from pyoxr import OXRClient
from flask import session, redirect
from functools import wraps
from math import pi
from bokeh.palettes import Category20
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.embed import components
from bokeh.models import Legend

import pandas as pd


def login_required(f):
    # login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Query Exchange Rate and Currencies from OpenExchange
def oex():
    oxr_cli = OXRClient(app_id="281e3d3bb93840828f7da169c7279b65")
    session['currencies'] = oxr_cli.get_currencies()
    session['rates'] = oxr_cli.get_latest()['rates']
    return


def line(x, y):
    """ Generate Line Graph """
    # Create plot
    p = figure(title="Monthly Expenses", x_axis_label='month', y_axis_label='expense')
    
    # Add line
    p.line(x, y, line_width=2)
    
    # Create results
    script, div = components(p)
    
    return script, div

def pie(x):
        """ Create pie graph """ 
        data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'tag'})
        data['angle'] = data['value']/data['value'].sum() * 2*pi
        data['color'] = Category20[len(x)]
        
        p = figure(height=420, width=640, title="Expense Distribution By Year", toolbar_location=None,
                tools="hover", tooltips="@tag", x_range=(-0.5, 1.0))
        
        p.wedge(x=0, y=1, radius=0.4,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color="white", fill_color='color', legend_field='tag', source=data)

        # Pie graph properties
        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None
        
        # Create pie graph
        script, div = components(p)
        
        return script, div
        

def bar(data, data_in, tags, months):
    # Create data for bar graph   
    p = figure(x_range=months, height=640, width=1080, title="Expense Distribution By Month",
           toolbar_location=None, tools="hover", tooltips="$name")

    v = p.vbar_stack(tags, x='month', width=0.8, color=Category20[len(data)-1], source=data)

    p.vbar(x=months, top=data_in, width=0.8, color="steelblue", name="CASH IN")
    
    #p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None

    legend = Legend(items=[(x, [v[i]]) for i, x in enumerate(tags)], location="center", orientation="horizontal")

    p.add_layout(legend, 'above')
    
    script, div = components(p)
    return script, div


        
# Filter
def money(value):
    """Format value."""
    return f"{value:,.2f}"