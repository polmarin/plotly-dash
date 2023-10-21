import numpy as np
import plotly.express as px
import plotly.graph_objects as go

class FootballPitch():
    # ALL THE VALUES ARE IN METERS
    PITCH_LENGTH_METERS = 105
    PITCH_WIDTH_METERS = 68
    HALF = False
    
    def __init__(self, 
                 pitch_length_meters = PITCH_LENGTH_METERS, 
                 pitch_width_meters = PITCH_WIDTH_METERS,
                 half = HALF
                ):
        self.pitch_length = pitch_length_meters
        self.pitch_width = pitch_width_meters
        self._vertical_margin = 5
        self._horizontal_margin = 5
        self.half = half

        if self.half:
            self.pitch_length /= 2
        
    
    def plot_pitch(self, show=True, plot_corner_arcs=False, line_color='white', bg_color='#60b922', zoom_ratio=1):
        # Fig to update
        fig = go.Figure()

        # Internal variables
        self.height_px = self.pitch_width*10*zoom_ratio
        self.width_px = self.pitch_length*10*zoom_ratio

        pitch_length_half = self.pitch_length/2 if not self.half else 0
        pitch_width_half = self.pitch_width/2
        corner_arc_radius = 1

        centre_circle_radius = 9.15
            
        goal = 7.32
        goal_area_width = goal + (5.5*2)
        goal_area_length = 5.5
        penalty_area_width = goal_area_width + (11*2)
        penalty_area_length = goal_area_length + 11
        penalty_spot_dist = 11
        penalty_circle_radius = 9.15

        # The pitch itself
        fig.add_trace(
            go.Scatter(
                x=[0, self.pitch_length, self.pitch_length, 0, 0], 
                y=[0, 0, self.pitch_width, self.pitch_width, 0], 
                mode='lines',
                hoverinfo='skip',
                marker_color=line_color,
                showlegend=False,
                fill="toself",
                fillcolor=bg_color
            )
        )
        
        # Corner arcs (ACABAR ELIMINANTHO)
        if plot_corner_arcs:
            for degrees in range(0, 360, 90):
                theta = np.linspace(degrees*np.pi/180, (degrees+90)*np.pi/180, 5000)
                x = corner_arc_radius * np.cos(theta)
                y = corner_arc_radius * np.sin(theta)
                if degrees in [90, 180]:
                    x += self.pitch_length
                if degrees in [180, 270]:
                    y += self.pitch_width
                fig.add_trace(
                    go.Scatter(
                        x=x, y=y, mode='lines', marker_size=1, hoverinfo='skip', marker_color=line_color, showlegend=False
                    )
            )
        
        # Add half-way line, centre spot and arc
        halfway_line = go.Scatter(
            x=[pitch_length_half, pitch_length_half], 
            y=[0, self.pitch_width], 
            mode='lines',
            hoverinfo='skip',
            marker_color=line_color,
            showlegend=False
        )
        centre_spot = go.Scatter(
            x=[pitch_length_half], 
            y=[pitch_width_half], 
            hoverinfo='skip',
            marker_color=line_color,
            marker_size=7,
            showlegend=False
        )
        fig.add_shape(
            type="circle",
            xref="x", 
            yref="y",
            x0=pitch_length_half - centre_circle_radius, 
            y0=pitch_width_half - centre_circle_radius, 
            x1=pitch_length_half + centre_circle_radius, 
            y1=pitch_width_half + centre_circle_radius,
            line_color=line_color,
            showlegend=False
        )
        

        # Add all inside the penalty area
        goal_lines_to_plot = [0, self.pitch_length] if not self.half else [self.pitch_length]
        for goal_line_x in goal_lines_to_plot:
            # Goal area
            fig.add_trace(
                go.Scatter(
                    x=[goal_line_x, abs(goal_line_x-goal_area_length), abs(goal_line_x-goal_area_length), goal_line_x, goal_line_x],
                    y=[
                        pitch_width_half - (goal_area_width/2), pitch_width_half - (goal_area_width/2), 
                        pitch_width_half + (goal_area_width/2), pitch_width_half + (goal_area_width/2), 
                        pitch_width_half - (goal_area_width/2)
                    ], 
                    mode='lines',
                    hoverinfo='skip',
                    marker_color=line_color,
                    showlegend=False
                )
            )

            # Penalty spot
            fig.add_trace(
                go.Scatter(
                    x=[abs(goal_line_x-penalty_spot_dist)], 
                    y=[pitch_width_half], 
                    hoverinfo='skip',
                    marker_color=line_color,
                    marker_size=5,
                    showlegend=False
                )
            )

            # Penalty area
            fig.add_trace(
                go.Scatter(
                    x=[goal_line_x, abs(goal_line_x-penalty_area_length), abs(goal_line_x-penalty_area_length), goal_line_x, goal_line_x],
                    y=[
                        pitch_width_half - (penalty_area_width/2), pitch_width_half - (penalty_area_width/2), 
                        pitch_width_half + (penalty_area_width/2), pitch_width_half + (penalty_area_width/2), 
                        pitch_width_half - (penalty_area_width/2)
                    ], 
                    mode='lines',
                    hoverinfo='skip',
                    marker_color=line_color,
                    showlegend=False
                )
            )

            # Penalty arc
            degree = 307 if goal_line_x == 0 else 127
            theta = np.linspace(degree*np.pi/180, (degree+106)*np.pi/180, 5000)
            x = penalty_circle_radius * np.cos(theta) + abs(goal_line_x-penalty_spot_dist)
            y = penalty_circle_radius * np.sin(theta) + pitch_width_half
            fig.add_trace(
                go.Scatter(
                    x=x, y=y, mode='lines', marker_size=1, hoverinfo='skip', marker_color=line_color, showlegend=False
                )
            )

        
        # Add the remaining traces
        for trace in [halfway_line, centre_spot]:
            fig.add_trace(trace)

        # Add final styles
        fig.update_layout(
            yaxis_range=[-self._vertical_margin, self.pitch_width + self._vertical_margin], 
            xaxis_range=[-self._horizontal_margin, self.pitch_length + self._horizontal_margin],
            height=self.height_px,
            width=self.width_px,
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, visible=False),
            yaxis=dict(showgrid=False, visible=False)
        )

        if show:
            fig.show()
        return fig

    
    def plot_heatmap(self, data: np.ndarray, zoom_ratio=1, **kwargs):
        if "colorscale" not in kwargs:
            kwargs["colorscale"] = px.colors.sequential.Reds[:1] + px.colors.sequential.Sunsetdark

        fig = self.plot_pitch(show=False, line_color='black', bg_color='rgba(0,0,0,0)', zoom_ratio=zoom_ratio)
        dx = self.pitch_length/ data.shape[1]
        dy = self.pitch_width / data.shape[0]
        
        heatmap = go.Heatmap(z=data,
                             dx=dx, dy=dy, y0=dy / 2, x0=dx / 2,
                             **kwargs
                            )
        fig.add_trace(heatmap)
        fig.update_layout(
            colorway=px.colors.sequential.Reds[:1]
        )
        
        return fig