"""Dataset for embedding checkpoints to train agent."""
from typing import Tuple

import cv2
import numpy as np
import torch
from skvideo.io import FFmpegReader
from torch.utils.data import Dataset


class VideoDataset(Dataset):
    """
    Dataset for embedding checkpoints to train agent.

    Parameters
    ----------
    filenames : list of str
        List of filenames of video files.
    trims : list of float
        List of tuples `(begin_idx, end_idx)` that specify what frame
        of the video to start and end.
    crops : list of tuple
        List of tuples `(x_1, y_1, x_2, y_2)` that define the clip
        window of each video.
    frame_rate : int
        Frame rate to sample video. Default to 15.

    """

    def __init__(
        self,
        filename: str,
        trim: Tuple[int, int],
        crop: Tuple[int, int, int, int],
        frame_rate: float = 15,
    ) -> None:
        super().__init__()

        # Get video frames with scikit-video
        reader = FFmpegReader(
            filename + ".mp4",
            inputdict={"-r": str(frame_rate)},
            outputdict={"-r": str(frame_rate)},
        )
        self.frames: np.ndarray = []
        for frame_idx, frame in enumerate(reader.nextFrame()):
            # Trim video (time)
            if frame_idx < trim[0]:
                continue
            if frame_idx >= trim[1]:
                break
            frame_idx += 1

            # Crop frames (space)
            frame = frame[crop[1] : crop[3], crop[0] : crop[2], :]
            self.frames.append(cv2.resize(frame, (140, 140)))

        # Change to NumPy array with PyTorch dimension format
        self.frames = np.array(self.frames, dtype=float)
        self.frames = np.transpose(self.frames, axes=(0, 3, 1, 2))

    def __len__(self) -> int:
        return len(self.frames) - 3

    def __getitem__(self, index: int) -> int:
        """
        Return a single framestack.

        Parameters
        ----------
        index : int

        Returns
        -------
        framestack : torch.FloatTensor

        """
        # Stack Frames
        framestack = self.frames[index : index + 4]

        # Center-crop Frames from 140x140 to 128x128
        # TODO Is center-cropping correct?
        y = 6
        x = 6
        framestack = framestack[:, :, y : y + 128, x : x + 128]

        # Switch 4 x 3 x 128 x 128 to 1 x 12 x 128 x 128
        framestack = torch.FloatTensor(framestack).view(-1, 128, 128)

        # Scale image values from 0~255 to 0~1
        # TODO Do in __init__
        framestack /= 255.0

        return framestack
