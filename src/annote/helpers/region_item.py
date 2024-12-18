import pyqtgraph as pg


class RegionItem(pg.LinearRegionItem):
    """
    A custom LinearRegionItem that is aware of the table it is being used in.
    """
    def __init__(self):
        """
        Initialize the RegionItem.
        """
        super(RegionItem, self).__init__()
        self.table_data = None
        self.table_widget = None

    def mouseClickEvent(self, ev):
        """
        Override the mouseClickEvent to select the corresponding row in the table.
        """
        for index, row in self.table_data.iterrows():
            for region in row['Regions']:
                if region == self:
                    self.table_widget.select_row(index)