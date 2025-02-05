class Piece:
    def __init__(self, name, directions, move_distance, owner, promoted=False):
        self.name = name
        self.directions = directions
        self.move_distance = move_distance
        self.owner = owner
        self.promoted = promoted