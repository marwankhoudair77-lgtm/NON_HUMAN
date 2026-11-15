from sqlalchemy.types import UserDefinedType
from sqlalchemy.ext.compiler import compiles


class PostGISMultiPolygon(UserDefinedType):
    """PostGIS MULTIPOLYGON column; compiles to TEXT only for SQLite-based unit tests."""
    cache_ok = True

    def get_col_spec(self, **kw):
        return "geometry(MULTIPOLYGON,4326)"


@compiles(PostGISMultiPolygon, "sqlite")
def compile_geometry_sqlite(type_, compiler, **kw):
    return "TEXT"
