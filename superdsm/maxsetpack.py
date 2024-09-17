import repype.status


def solve_maxsetpack(objects, status=None):
    accepted_objects  = []  ## primal variable
    remaining_objects = list(objects)

    w = lambda c: c.energy
    while len(remaining_objects) > 0:

        # choose the best remaining object
        best_object = max(remaining_objects, key=w)
        accepted_objects.append(best_object)

        # discard conflicting objects
        remaining_objects = [c for c in remaining_objects if len(c.footprint & best_object.footprint) == 0]

    repype.status.update(status, f'MAXSETPACK - GREEDY accepted objects: {len(accepted_objects)}')
    return accepted_objects
