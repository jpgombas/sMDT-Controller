import math
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import io
import base64
from typing import List, Optional
from matplotlib.ticker import MultipleLocator

# Constants
TUBES_PER_ROW = 12
TUBE_SEPARATION = 1
OFFSET = 0.5
ROW_SEPARATION = 1.0
TUBE_RADIUS = 1.0

class ReconstructionAlg:

    @staticmethod
    def convert_to_spherical(theta1, theta2) -> tuple:
        """
        Convert angles theta1 (xz-plane, from x-axis) and theta2 (yz-plane, from y-axis)
        to spherical coordinates (theta, phi).
        
        Args:
            theta1 (float): Angle in radians between xz-plane projection and x-axis
            theta2 (float): Angle in radians between yz-plane projection and y-axis
        
        Returns:
            tuple: (theta, phi) in radians, where theta is polar angle from z-axis,
                phi is azimuthal angle from x-axis
        """
        # Handle edge cases where angles might be too small
        if abs(theta1) < 1e-10:
            theta1 = 1e-10
        if abs(theta2) < 1e-10:
            theta2 = 1e-10
            
        # Calculate tan^2(theta) = 1/tan^2(theta1) + 1/tan^2(theta2)
        tan_theta_sq = 1 / (math.tan(theta1) ** 2) + 1 / (math.tan(theta2) ** 2)
        theta = math.atan(math.sqrt(tan_theta_sq))
        
        # Calculate phi = arctan(tan(theta1) / tan(theta2))
        phi = math.atan2(math.tan(theta1), math.tan(theta2))
        
        # Ensure theta is in [0, pi]
        if theta < 0:
            theta += math.pi
            
        # Ensure phi is in [0, 2pi]
        if phi < 0:
            phi += 2 * math.pi
            
        return theta, phi

    @staticmethod
    def tubeID_to_x(tube_id: int) -> float:
        """
        Convert a tube ID to its x-position in a grid of tubes.
        """
        row = tube_id // TUBES_PER_ROW
        column = tube_id % TUBES_PER_ROW

        x_position = column * TUBE_SEPARATION
        if row % 2 == 0:
            x_position += OFFSET

        return x_position

    @staticmethod
    def tubeID_to_y(tube_id: int) -> float:
        """
        Convert a tube ID to its y-position in a grid of tubes.
        """
        row = tube_id // TUBES_PER_ROW
        y_position = row * ROW_SEPARATION
        return y_position

    def tubeIDs_to_coordinates(self, tube_ids: list) -> list[tuple[float, float]]:
        """
        Convert a list of tube IDs to a list of (x, y) coordinates.
        """
        coordinates = []
        for tube_id in tube_ids:
            x = self.tubeID_to_x(tube_id)
            y = self.tubeID_to_y(tube_id)
            coordinates.append((x, y))
        return coordinates

    def fit_line(self, tube_ids: list) -> float:
        """
        Fit a linear model to the coordinates and return angle.
        """
        if len(tube_ids) < 2:
            return 0.0
            
        coordinates = self.tubeIDs_to_coordinates(tube_ids)
        x_vals, y_vals = zip(*coordinates)
        
        # Handle case where all x values are the same (vertical line)
        if len(set(x_vals)) == 1:
            return math.pi / 2  # 90 degrees
            
        coefficients = np.polyfit(x_vals, y_vals, 1)
        return np.arctan(coefficients[0])

    def fit_line_through_circles(self, tube_ids: list, radii: list) -> tuple:
        """
        Fit a line that aims to intersect all given circles.
        """
        if len(tube_ids) < 2 or len(tube_ids) != len(radii):
            raise ValueError("Need at least 2 tubes and matching radii")
            
        coordinates = self.tubeIDs_to_coordinates(tube_ids)
        x = np.array([coord[0] for coord in coordinates])
        y = np.array([coord[1] for coord in coordinates])
        r = np.array(radii)

        def cost(params: np.ndarray, x: np.ndarray, y: np.ndarray, r: np.ndarray) -> float:
            m, b = params
            # Distance from circle center to the line y = mx + b
            dist = np.abs(y - m * x - b) / np.sqrt(1 + m**2)
            # Violation is the distance from the edge of the circle to the line
            violations = np.abs(r - dist)
            return np.sum(violations ** 2)

        # Better initial guess based on simple line fit
        try:
            simple_angle = self.fit_line(tube_ids)
            initial_m = math.tan(simple_angle)
        except:
            initial_m = 0.0
            
        # Initial intercept guess
        y_center = np.mean(y)
        x_center = np.mean(x)
        initial_b = y_center - initial_m * x_center
        
        initial_params = np.array([initial_m, initial_b])

        try:
            result = minimize(cost, initial_params, args=(x, y, r), method='BFGS')
            if result.success:
                m, b = result.x
                return m, b
            else:
                # Fallback to simple line fit
                return initial_m, initial_b
        except:
            return initial_m, initial_b
    
    def calibrated_radius(self, tof: float, tot: float) -> float:
        """
        Convert time of flight and time over threshold into a radial parameter.
        TODO: Fix this function with data that comes from the sMDT chambers.
        """
        a, b, c = -2, 2e-2, 2e-2
        x = tof
        y = tot

        poly = a + b*x + c*y
        # Fixed exponential function
        return 1 / (1 + math.exp(-poly))

    def reconstruct_event(self, hits: List[dict]) -> Optional[dict]:
        """
        Reconstruct a muon track from detector hits.
        
        Args:
            hits: List of hit dictionaries with keys 'tube_number', 'time_of_flight', 'time_over_threshold'
            
        Returns:
            Dictionary with reconstruction results or None if reconstruction fails
        """
        if len(hits) < 4:  # Need at least 4 hits for good reconstruction
            return None
            
        try:
            # Separate hits by chamber
            chamber0_hits = [hit for hit in hits if hit['chamber'] == 0]
            chamber1_hits = [hit for hit in hits if hit['chamber'] == 1]
            
            if len(chamber0_hits) < 3 or len(chamber1_hits) < 3: # Need at least two hits in each detector
                return None
                
            # Get tube IDs and calculate radii for each chamber
            tube_ids_0 = [hit['tube_number'] for hit in chamber0_hits]
            tube_ids_1 = [hit['tube_number'] for hit in chamber1_hits]
            
            radii_0 = [self.calibrated_radius(hit['time_of_flight'], hit['time_over_threshold']) 
                      for hit in chamber0_hits]
            radii_1 = [self.calibrated_radius(hit['time_of_flight'], hit['time_over_threshold']) 
                      for hit in chamber1_hits]
            
            # Fit lines through circles for each chamber
            m1, b1 = self.fit_line_through_circles(tube_ids_0, radii_0)
            m2, b2 = self.fit_line_through_circles(tube_ids_1, radii_1)
            
            # Convert to angles
            angle1 = np.arctan(m1)
            angle2 = np.arctan(m2)
            
            # Convert to spherical coordinates
            theta, phi = self.convert_to_spherical(angle1, angle2)
            
            return {
                'chamber0_hits': len(chamber0_hits),
                'chamber1_hits': len(chamber1_hits),
                'angle1_deg': math.degrees(angle1),
                'angle2_deg': math.degrees(angle2),
                'theta_deg': math.degrees(theta),
                'phi_deg': math.degrees(phi),
                'line_params_0': (m1, b1),
                'line_params_1': (m2, b2),
                'tube_ids_0': tube_ids_0,
                'tube_ids_1': tube_ids_1,
                'radii_0': radii_0,
                'radii_1': radii_1
            }
            
        except Exception as e:
            print(f"Reconstruction failed: {e}")
            return None

    def plot_reconstruction(self, reconstruction_data: dict, chamber: int = 0) -> str:
        """
        Create a visualization of the reconstruction for one chamber.
        
        Args:
            reconstruction_data: Output from reconstruct_event
            chamber: Which chamber to plot (0 or 1)
            
        Returns:
            Base64 encoded PNG image string
        """
        try:
            if chamber == 0:
                tube_ids = reconstruction_data['tube_ids_0']
                radii = reconstruction_data['radii_0']
                m, b = reconstruction_data['line_params_0']
                angle = reconstruction_data['angle1_deg']
            else:
                tube_ids = reconstruction_data['tube_ids_1']
                radii = reconstruction_data['radii_1']
                m, b = reconstruction_data['line_params_1']
                angle = reconstruction_data['angle2_deg']
                
            coordinates = self.tubeIDs_to_coordinates(tube_ids)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Plot circles and centers
            for (x, y), r in zip(coordinates, radii):
                circle = Circle((x, y), r, fill=False, edgecolor='blue', linewidth=2)
                ax.add_patch(circle)
                ax.plot(x, y, 'ro', markersize=8)  # Mark center
                
            # Plot the fitted line
            x_line = np.linspace(-1, 12, 100)
            y_line = m * x_line + b
            ax.plot(x_line, y_line, 'g-', linewidth=3, label=f'Fitted line (θ={angle:.1f}°)')
            
            ax.set_aspect('equal')
            if chamber == 0:
                ax.set_xlabel('X')
            else:
                ax.set_xlabel('Y')
            
            ax.set_ylabel('Height')
            plt.gca().xaxis.set_major_locator(MultipleLocator(1))
            plt.gca().yaxis.set_major_locator(MultipleLocator(1))
            ax.grid(True, alpha=0.2)
            
            # Set reasonable limits
            ax.set_xlim(-1, 12)
            ax.set_ylim(-1, 8)
            
            # Convert to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
            
        except Exception as e:
            print(f"Plotting failed: {e}")
            return ""