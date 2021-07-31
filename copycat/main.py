import argparse
from os import path

from copycat.debugging.debugging import debug_params
from copycat.global_types import Bounds, Clef
from copycat.image_processing.key_extraction import get_piano_keys
from copycat.image_processing.note_press_detection import NoteDetector
from copycat.image_processing.paino_key import PianoKey
from copycat.media_parsing.video_to_frames import Video
from copycat.notation.notation import Notation


def main(
        file_path: str,
        bounds: Bounds,
        first_note: str,
        skip_frames: int,
        detector_line_offset: int,
        tempo: int,
        min_note_speed: int,
        debug: bool
):
    video = Video(file_path)
    frames = video.extract_frames()

    for i in range(skip_frames):
        next(frames)

    control_frame = next(frames)

    keys = get_piano_keys(control_frame, bounds, PianoKey.note_to_index(first_note))
    detector = NoteDetector(control_frame, bounds.y + detector_line_offset, 0.1)

    if debug:
        debug_params(control_frame, frames, keys, detector, bounds)
        return

    n = Notation(fps=video.fps, tempo=tempo, octave_offset=0, min_note_speed=min_note_speed)
    try:
        for frame in frames:
            for key in keys.values():
                clef = detector.is_note_detected(key.contour, frame)
                if clef is not Clef.NONE:
                    n.push_note(key.note, clef=clef)
            n.apply_frame()
    except Exception:
        print(n.get_abc_notation(title=path.basename(file_path), composer=""))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="The path of the mp4 synthesia video", metavar="PATH", required=True)
    parser.add_argument("-t", "--tempo", help="The tempo of the piece in BPM", default=120, type=int)
    subparsers = parser.add_subparsers()
    manual = subparsers.add_parser("manual")
    manual.add_argument("--bounds", help="The boundaries around the piano keys space separated",
                        metavar="X Y WIDTH HEIGHT", required=True)
    manual.add_argument("--first-key", help="The first white key in the bounds.", metavar="NOTE", required=True)
    manual.add_argument("--skip-frames", help="How many frame to skip in case there is an introduction", default=0,
                        type=int)
    manual.add_argument("--detector-line-offset",
                        help="Number of pixels from the top of the boundary to offset the detector line", type=int,
                        default=80)
    manual.add_argument("--min-speed", help="Defines a minimum note duration", type=int, default=2)
    manual.add_argument("--debug", help="Show debugged version", default=False, action="store_true")
    args = parser.parse_args()
    main(file_path=args.file, bounds=Bounds(*[int(v) for v in args.bounds.split(" ")]), first_note=args.first_key,
         skip_frames=args.skip_frames, detector_line_offset=args.detector_line_offset, tempo=args.tempo,
         debug=args.debug, min_note_speed=args.min_speed)
