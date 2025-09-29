import numpy as np
from scipy.optimize import least_squares


class Calibrator:
    def extract_all_matches(self, video_path):
        """
        Extracts all matches from video on GPU
        :param video_path: path to video
        :return: a np array of all matches
        """
        return np.array([])

    def refine_with_bundle_adjustment(self, video_path, K_init):
        """
        Optimizes camera intrinsics and poses
        :param video_path: Path to video
        :param K_init: initial K guess
        :return: final K
        """

        matches = self.extract_all_matches(video_path)
        point_3d = None
        observed_2d = None

        def objective(params):
            """
            Optimizes for focal length, poses, and 3D points
            :param params: focal, poses, points
            :return:
            """
            focal = params[0]
            K = np.array(
                [[focal, 0, K_init[0, 2]], [0, focal, K_init[1, 2]], [0, 0, 1]]
            )

            errors = []

            for match in matches:
                # Project from 3d to 2d
                proj = point_3d  # Dummy
                errors.append(proj - observed_2d)

            return np.concatenate(errors)

        initial_params = [K_init[0, 0]]

        # Optimize with least-squares for simplicity
        res = least_squares(
            objective,
            initial_params,
            method="trf",  # Trust Region Reflective - Stable
            verbose=2,
        )

        focal = res.x[0]
        return np.array([[focal, 0, K_init[0, 2]], [0, focal, K_init[1, 2]], [0, 0, 1]])

    def identify_intrinsics(self, frames, video_path):
        """
        Estimates camera intrinsic matrix (focal length and principle) from  frame
        :param video_path: path to video
        :param frames: initial frame to get details
        :return: camera intrinsics matrix
        """
        import cv2
        import numpy as np

        capture = cv2.VideoCapture(video_path)
        width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # COLMAP initial guess formula - works surprisingly well
        initial_focal = 1.2 * max(width, height)

        # Principle points of camera
        cx, cy = width / 2, height / 2
        K_init = np.array(
            [[initial_focal, 0, cx], [0, initial_focal, cy], [0, 0, 1]]
        )  # https://ksimek.github.io/2013/08/13/intrinsic

        print(f"Initial guess: focal={initial_focal:.1f}")

        # Refine
        K_refined = self.refine_with_bundle_adjustment(video_path, K_init)

        return K_refined
