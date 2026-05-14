def compute_distances_to_curve(centroids, attractor_curve):
    if attractor_curve is None:
        return [0.0 for _ in centroids]
    return [attractor_curve.DistanceTo(point) for point in centroids]


def select_closest_indices(distances, closest_count):
    count = max(0, int(closest_count))
    sorted_indices = sorted(range(len(distances)), key=lambda i: distances[i])
    return sorted_indices[:min(count, len(distances))]


def remap_values(values, domain_start, domain_end):
    if not values:
        return []
    start = float(domain_start)
    end = float(domain_end)
    minimum = min(values)
    maximum = max(values)
    span = end - start
    if maximum == minimum:
        return [start + span * 0.5 for _ in values]
    return [start + ((value - minimum) / (maximum - minimum)) * span for value in values]
