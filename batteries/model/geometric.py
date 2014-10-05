from geoalchemy2.shape import from_shape, to_shape
from geoalchemy2 import Geometry
from shapely.geometry.point import Point
from sqlalchemy import event


class Geometric(object):
    pass


@event.listens_for(Geometric, 'mapper_configured', propagate=True)
def configure_geometric(mapper, target):
    for k, column in mapper.columns.items():
        property = getattr(target, k)
        if property.is_attribute and type(column.type) is Geometry:
            if column.type.geometry_type.lower() == 'point':
                setattr(target, k, PointGeometryDescriptor(property))


class PointGeometryDescriptor(object):
    """descriptor for 2D point geometry"""

    def __init__(self, property):
        self.property = property

    def __get__(self, instance, cls=None):
        if instance is not None:
            wkb = self.property.__get__(instance, cls)
            if wkb is None:
                return None
            return to_shape(wkb)

        elif cls is not None:
            return self.property.__get__(instance, cls)

    def __set__(self, instance, v):
        p = Point(*v)
        self.property.__set__(instance, from_shape(p))


def Point_repr(point):
    p = [point.x, point.y]
    if point.has_z:
        p.append(point.z)

    return "<Point {}>".format(', '.join(map(str, p)))


def Point_to_wkb(point):
    return from_shape(point)

Point.__repr__ = Point_repr
Point.to_wkb = Point_to_wkb
