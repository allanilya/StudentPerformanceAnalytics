# Author: Allan Ilyasov
# Title: Student Performance Analytics Dashboard: Portuguese Language Course
# Dataset: Student Alcohol Consumption
# Source: https://www.kaggle.com/datasets/uciml/student-alcohol-consumption
#
# This dashboard is focused on analyzing data from student-por.csv (Portuguese language course), 
# which has a larger sample size of students. There are many factors explored, such as how study time, 
# internet access, and alcohol consumption relate to student GPA (out of 100).

#import the relevant library
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

#Import the relevant library and dataset.
file_path = 'student-por.csv'  # Replace with your filepath
data = pd.read_csv(file_path)

data['studytime'] = pd.Categorical(
    data['studytime'].map({
        1: '<2 hours',
        2: '2-5 hours', 
        3: '5-10 hours',
        4: '>10 hours'
    }),
    categories=['<2 hours', '2-5 hours', '5-10 hours', '>10 hours'],
    ordered=True
)

# Chose the max value of alcohol consumption between weekday and weekend consumption
data['consumptionlevel'] = data[['Dalc', 'Walc']].max(axis=1)

# Changed the scale to become out of 100 instead of 20
data['GPA'] = data['G3'] * 5 

# Renamed 'higher' to 'higher education' for clarity
data['higher education']= data['higher']

# Renamed the data values for clarity
data['sex'] = data['sex'].replace({'F': 'Female', 'M': 'Male'})
                                                      
selected_data = data.loc[:, ['sex', 'studytime', 'internet', 'higher education','failures', 
                             'freetime', 'traveltime', 'consumptionlevel', 'absences', 'GPA']].copy()
# Creation of filtered dataset complete
selected_data.to_csv('student_alcohol_cleaned.csv', index=False)

# Figure Generation Function
def generate_figures(filtered_data, grouped_data):
    """
    This function creates all the figures we need for the dashboard.
    We have 8 charts:
    1) Box plot: GPA by Alcohol Consumption Level (using grouped_data)
    2) Line chart: GPA vs. Study Time (using filtered_data)
    3) Bar chart: Alcohol Consumption by Gender (using filtered_data)
    4) Histogram: Distribution of Absences (using filtered_data)
    5) Sunburst: GPA by Study Time and Internet Access (using filtered_data)
    6) Violin plot: GPA by Internet Access (using filtered_data)
    7) Scatter plot: Alcohol Consumption vs. GPA (using grouped_data)
    
    'filtered_data': raw, filtered data points
    'grouped_data': data that is already averaged or summarized.
    """

    # 1. Sunburst: Shows how GPA breaks down by study time category and internet access.
    # This helps visualize how multiple factors combine to affect GPA.
    grouped_sun = filtered_data.groupby(['studytime','internet'], observed=True)['GPA'].mean().reset_index()
    fig_sunburst = px.sunburst(
        grouped_sun,
        path=['studytime', 'internet'],
        values='GPA',
        color='GPA',
        color_continuous_scale='blues',
        title='Academic Performance (GPA) by Study Time and Internet Access',
        labels={
            'studytime': 'Study Time',
            'internet': 'Internet Access (Yes/No)',
            'GPA': 'GPA (out of 100)'
        }
    )
    fig_sunburst.update_layout(
        width=800,
        height=600
    )
    
    # 2. Scatter plot with trendline: Shows how GPA changes with Alcohol Consumption Level.
    # The size of the points represents absences. A trendline helps us see if there's a pattern.
    fig_scatter= px.scatter(
        grouped_data,
        x='consumptionlevel',
        y='GPA',
        size='absences',
        trendline='ols',
        labels={
            'consumptionlevel': 'Alcohol Consumption Level (1-5 scale)',
            'GPA': 'GPA (out of 100)',
            'absences': 'Number of Absences',
        },
        title='Student Alcohol Consumption vs. GPA with Linear Regression'
    )
    fig_scatter.update_layout(
        template='plotly_white'
    )
    fig_scatter.update_layout(
        width=800, 
        height=600
    )

    # Alcohol consumption into categories (Low, Medium, High) for the box plot.
    consumption_levels = ['Low', 'Medium', 'High']
    filtered_data['consumption_level'] = pd.cut(
        filtered_data['consumptionlevel'],
        bins=3,
        labels=consumption_levels,
        include_lowest=True
    )
    # 3. Box plot: helps visualize if there are differences in academic performance based on drinking habits
    fig_box = px.box(
        filtered_data,
        x='consumption_level',
        y='GPA',
        color='consumption_level',
        labels={
            'consumption_level': 'Alcohol Consumption Level ',
            'GPA': 'Academic Performance (GPA out of 100)'
        },
        title='GPA Distribution by Alcohol Consumption Level',
    )
    fig_box.update_layout(
        xaxis_title='Alcohol Consumption Level',
        yaxis_title='Academic Performance (GPA)',
        showlegend=False,
        template='plotly_white',
        width=800,
        height=600
    )

    # 4. Line chart: Shows the trend of academic performance across different study time.
    # Grouped the dataset by study time and aggregated the mean GPA for each category.
    studytime_gpa = filtered_data.groupby('studytime').agg({'GPA': 'mean'}).reset_index()
    studytime_gpa['studytime'] = pd.Categorical(
        studytime_gpa['studytime'],
        categories=['<2 hours', '2-5 hours', '5-10 hours', '>10 hours'],
        ordered=True
    )
    # Sorting by study time ensures the line chart connects points in the correct order.
    studytime_gpa = studytime_gpa.sort_values('studytime')
    fig_line = px.line(
        studytime_gpa,
        x='studytime',
        y='GPA',
        markers=True,
        labels={
            'studytime': 'Study Time Categories',
            'GPA': 'Average GPA (out of 100)'
        },
        title='Trend of Academic Performance Across Study Time',
    )
    fig_line.update_layout(
        width=800,
        height=600,
        template='plotly_white'
    )

    # 5. Bar chart: Shows average alcohol consumption by gender.
    # Grouped the data by gender and calculated mean alcohol consumption and GPA for each group
    gender_groups = filtered_data.groupby('sex').agg({'consumptionlevel': 'mean', 'GPA': 'mean'}).reset_index()
    fig_bar = px.bar(
        gender_groups,
        x='sex',
        y='consumptionlevel',
        labels={
            'consumptionlevel': 'Alcohol Consumption (1=very low, 5=very high)',
            'sex': 'Gender',
        },
        title='Mean Student Alcohol Consumption by Gender',
        color='sex',
        hover_data={'GPA': ':.2f'},
        template='plotly_dark'
    )
    fig_bar.update_layout(
        width=800,
        height=600
    )

    # 6. Histogram: Shows how many students have various numbers of absences.
    # This helps us see if absences are common or rare.
    fig_hist = px.histogram(
        filtered_data,
        x='absences',
        nbins=10,
        labels={'absences': 'Number of Absences'},
        title='Distribution of Student Absences'
    )
    fig_hist.update_layout(
        xaxis_title='Number of Absences',
        yaxis_title='Count of Students',
        template='plotly_dark',
        width=800,
        height=600
    )

    # 7. Violin plot: to show the distribution of GPA scores by higher education aspirations
    # This helps to see if there are differences in academic performance based on aspirations
    fig_violin = px.violin(
        filtered_data,
        x='higher education',
        y='GPA',
        color='higher education', 
        box=True,  
        points='all',  
        title='Distribution of GPA by Higher Education Aspirations',
        template='plotly_white',
        labels={
            'higher education': 'Wants to Take Higher Education',
            'GPA': 'GPA (out of 100)'
        }
    )
    fig_violin.update_layout(
        width=1000, 
        height=600
    )
    fig_violin.update_traces(meanline_visible=True) 


    # Returning all the figures as a dictionary so we can easily access them in the callback
    return {
        'sunburst': fig_sunburst,
        'scatter': fig_scatter,
        'box': fig_box,
        'line': fig_line,
        'bar': fig_bar,
        'hist': fig_hist,
        'violin': fig_violin        
    }


# Dash Application Setup
# Dash app is initializred using a Bootstrap theme for easy styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    # Title
    dbc.Row([
        dbc.Col(html.H1("Student Performance Analytics Dashboard:",
                        className="text-center mb-4"), width=12),
        dbc.Col(html.H2("Portuguese Language Course",
                        className="text-center mb-4"), width=12)
    ]),

    # Gender Filter
    dbc.Row([
        dbc.Col([
            html.Label("Select Gender:"),
            dcc.Dropdown(
                id='gender-filter',
                options=[
                    {'label': 'All', 'value': 'All'},
                    {'label': 'Male', 'value': 'Male'},
                    {'label': 'Female', 'value': 'Female'}
                ],
                value='All',
                clearable=False
            ),
            html.Br(),
            html.P("Use the dropdown to filter the data by gender. The charts will update accordingly.")
        ], width=12)
    ]),
    
    # Sunburst
    dbc.Row([
        dbc.Col(dcc.Graph(id='sunburst-plot'), width=12)
    ]),
    
    # Scatter Plot
    dbc.Row([
        dbc.Col(dcc.Graph(id='scatter-plot'), width=12)
    ]),

    # Box Plot
    dbc.Row([
        dbc.Col(dcc.Graph(id='box-plot'), width=12)
    ]),

    # Line Chart
    dbc.Row([
        dbc.Col(dcc.Graph(id='line-chart'), width=12)
    ]),

    # Bar Chart
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-chart'), width=12)
    ]),

    # Histogram
    dbc.Row([
        dbc.Col(dcc.Graph(id='hist-plot'), width=12)
    ]),


    # Violin Plot
    dbc.Row([
        dbc.Col(dcc.Graph(id='violin-plot'), width=12)
    ])
], fluid=True)

# Callback Function
# This callback updates all the charts whenever the user changes the gender filter
# The callback takes the selected gender as input and outputs all the updated figures
@app.callback(
    [
        Output('sunburst-plot', 'figure'),
        Output('scatter-plot', 'figure'),
        Output('box-plot', 'figure'),
        Output('line-chart', 'figure'),
        Output('bar-chart', 'figure'),
        Output('hist-plot', 'figure'),
        Output('violin-plot', 'figure')        
    ],
    Input('gender-filter', 'value')
)
def update_plots(selected_gender):
    """
    This function filters the data based on the chosen gender.
    If 'All' is chosen, it uses the entire dataset.
    If 'Male' or 'Female' is chosen, it uses only that subset.
    Then it groups the filtered data for some of our aggregated charts.
    Finally, it calls 'generate_figures' to produce updated charts.
    """

    # Filter the dataset based on the selected gender
    if selected_gender == 'All':
        filtered_data = selected_data.copy()
    else:
        filtered_data = selected_data[selected_data['sex'] == selected_gender].copy()

# Group the data by key variables and calculated mean values for numeric columns
    grouped_data = filtered_data.groupby(['sex', 'studytime', 'internet', 'higher education'], observed=True).agg({
        'consumptionlevel': 'mean',
        'failures': 'mean',
        'absences': 'mean',
        'GPA': 'mean',
    }).reset_index()

    # Generate the updated figures with the new filtered and grouped data
    # By passing both data frames in the head, the figures can acees either filtered_data or grouped_data
    figs = generate_figures(filtered_data, grouped_data)
    return (figs['sunburst'], figs['scatter'], figs['box'], figs['line'], figs['bar'], figs['hist'],
            figs['violin'])


# Run the Dash app
if __name__ == '__main__':
    server = app.run_server(debug=True)

