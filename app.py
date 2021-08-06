import pandas as pd
import plotly.express as px
import numpy_financial as npf

import dash
import dash_core_components as dcc
import dash_table
import dash_html_components as html
from dash.dependencies import Input, Output

from dash.exceptions import PreventUpdate

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# ---------- Import and clean data (importing csv into pandas)

db = pd.read_csv(r'C:\Users\jasli\OneDrive\Desktop\Important\Education\Python\Project\Solar Viability - Copy.csv')
cost_per_kw = 75000.00
usage_period = 25
per_panel = 0.44
units = [30.0, 70.0, 100.0]
cost = [4.0, 5.45, 7.0, 8.05]
mthly_avg_india = 120.0
# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([
    html.Div([
    html.Div([
    html.Div([
        html.H2("Return on Investment from the purchase of solar panels", style={'text-align':'center', 'padding-left': '20px'}),
        html.Div([
            html.Br(),
            html.Br(),
            html.H6("Find out how much you can save per year:", style={'text-align': 'left','padding-left':'5px'}),
            html.Br(),
            html.Div(["Avg. electricity bill per month:    ",
            dcc.Input(id='my_bill', value='{}', type='number')], style={'text-align': 'left', 'padding-left': '5px'}),
            html.Br(),
            html.Div(["No. of panels to be installed:    ",
                dcc.Input(id='panels', value='{}', type='number')], style={'text-align': 'left','padding-left':'5px'}),
            html.Br(),
            html.Button(id='my-button', children="Calculate annual savings"),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
        ],
        style={'width': '43%', 'display': 'inline-block', 'padding-left': '210px', 'float': 'center'}),

        html.Div([
            html.Br(),
            html.Br(),
            html.H6("Average rates charged by electricity suppliers: "),
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in db.columns],
                data=db.to_dict('records'),
                style_header={
                    'backgroundColor': 'light blue',
                    'fontWeight': 'bold'},
                style_cell={
                    'minWidth': '180px',
                },
                style_data={
                    'border': '0.2px solid black',
                    'padding-right': '7px'
                }),
            html.Br(),
            dcc.Markdown('''
            **Output per solar panel**: 0.44 KW
            
            **Cost per KW**: 75,000 INR
            
            >1KW generates 120KW/hr (energy) per month
            '''),
            html.Br(),
        ],
        style={'width': '40', 'display': 'inline-block', 'float': 'right', 'padding-right': '210px'}),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div([
        html.Div(id='my_output', children=[], style={'text-align': 'center', 'color': 'blue'}),
        html.Div(id='irr', children=[], style={'text-align': 'center', 'color': 'red'}),
        html.Br(),
        html.Br(),
        ],
            style={'float': 'center'}),
    ],
        style={'float': 'center'}),
    ],
        style={'float': 'center'}),
        html.Div([
            dcc.Graph(id='my_graph')
        ],
        style={'float': 'left', 'padding-left': '400px'}),
],
    style={'float': 'center'}) #-- don't touch this '
])



@app.callback(
    Output(component_id='my_output', component_property='children'),
    Output(component_id='irr', component_property='children'),
    Output(component_id='my_graph', component_property='figure'),
    Input(component_id='panels', component_property='value'),
    Input(component_id='my-button', component_property='n_clicks'),
    Input(component_id='my_bill', component_property='value'),
)

def savings(solar_panels, clicks, bill):
    if clicks is None:
        raise PreventUpdate
    else:
        power,slab_list = get_power_from_bill(bill)
        capacity = float(solar_panels) * per_panel
        mthly_output = capacity * mthly_avg_india
        reduced_power = power - mthly_output
        mthly_savings = bill - get_bill_from_power(reduced_power, slab_list)
        if mthly_savings > 0:
            ann_savings = round(12 * mthly_savings, 2)
            #outputs
            irr_list, sp = get_data_for_graph(bill, reduced_power, slab_list)
            annual_savings = get_annual_savings_for_graph(bill, sp)
            fig = irr_graph(irr_list, sp, reduced_power, slab_list)
            user_irr = single_irr(ann_savings, solar_panels)
            return "Annual savings: INR {}".format(ann_savings), "IRR over 25y for panels installed: {}".format(user_irr), fig
        else:
            return "Current bill is low and you may not benefit from {} solar panels".format(solar_panels)


def irr_graph(y, x, reduced_power, slab_list):
    sp = []

    for i in range(1, x + 1):
        sp += [i]
    bill_new = get_bill_from_power(reduced_power, slab_list)
    while bill_new > 0:
        bill_new = 0
        fig1 = px.line(x=sp,
                       y=y,
                       title='IRR vs solar panels based on your bill', width=750, height=500,
                       )
    return fig1


def get_data_for_graph(bill, reduced_power, slab_list):
    irr_list = []
    bill_new = get_bill_from_power(reduced_power, slab_list)
    for i in range(1, 8):
        cash_flows = []
        initial_i = -(i * per_panel * cost_per_kw)
        cash_flows += [initial_i]
        for j in range(usage_period):
            cash_flows.append(get_annual_savings_for_graph(bill, i))
        #while bill_new:
        irr_list += [round(npf.irr(cash_flows), 4)]

    print(irr_list)


    return irr_list, i

def get_annual_savings_for_graph(bill, sp):
    power_consumed, slab_list = get_power_from_bill(bill)
    total_solar_capacity = sp * per_panel
    mthly_solar_output = total_solar_capacity * mthly_avg_india
    reduced_power = power_consumed - mthly_solar_output
    mthly_savings = bill - get_bill_from_power(reduced_power, slab_list)
    annual_savings = round(12 * mthly_savings, 2)

    return annual_savings

def single_irr(annual_savings, solar_panels):
    initial_investment = -solar_panels * per_panel * cost_per_kw  # Negative, since it results in an outflow of cash
    cashflows = [initial_investment]

    for i in range(usage_period):
        cashflows += [annual_savings]

    # Calculate the IRR
    internal_rate_return = round(npf.irr(cashflows), 4)
    return internal_rate_return

def get_power_from_bill(bill):
    sum_cost = 0
    power_consumed = 0
    j = 0
    slab = 1
    slab_list = []
    while j < len(units):
        sum_cost = sum_cost + units[j] * cost[j]
        j = j + 1
        slab_list += [sum_cost]
        if bill >= sum_cost:
            slab += 1
    if slab == 1:
        bill = bill / cost[0]
    else:
        bill = (bill - slab_list[slab - 2]) / cost[slab - 1]
        while slab > 1:
            bill += units[slab - 2]
            slab -= 1
    power_consumed += float(bill)

    return power_consumed,slab_list

def get_bill_from_power(reduced_power, slab_list):
    power_slab = 1
    bill_from_power = 0
    cum_units = 0
    units_list = []
    b = 0
    while b < len(units):
        cum_units += units[b]
        b = b + 1
        units_list += [cum_units]
    for i in units_list:
        if reduced_power > i:
            power_slab += 1
    if power_slab == 1:
        bill_from_power += reduced_power * cost[0]
    else:
        bill_from_power += slab_list[power_slab - 2] + (reduced_power - units_list[power_slab - 2]) * cost[power_slab - 1]

    return bill_from_power

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)

