"""
Custom DBF field parser to handle unknown field types.
"""
from dbfread.field_parser import FieldParser

class CustomFieldParser(FieldParser):
    """Custom field parser that handles unknown field types."""
    
    def __init__(self, dbf, memo=None):
        super().__init__(dbf, memo)
    
    def field_type_supported(self, field_type):
        """Override to handle unknown field types."""
        # Always return True to handle any field type
        return True
    
    def parse(self, field, data):
        """Parse field data."""
        try:
            # Try to use the standard parser first
            return super().parse(field, data)
        except ValueError:
            # For unsupported types, just return the raw data as a string
            if hasattr(data, 'decode'):
                # If it's bytes, decode it
                try:
                    return data.decode(self.dbf.encoding, errors=self.dbf.char_decode_errors)
                except UnicodeDecodeError:
                    # If decoding fails, return as hex to avoid further errors
                    return f"0x{data.hex()}"
            return str(data)
