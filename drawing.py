from PIL import Image, ImageDraw


class Drawing:
    def __init__(self, color, width, pt_list=[], id_=-1):
        self.pt_list = pt_list.copy()
        self.id_list = []

        self.id = id_  # id of the whole drawing in the sql db, not an id of a stroke on the canvas

        self.color = color
        self.width = width

    def add_point(self, point):
        '''
        Recives a point as a tuple adds it to its list
        '''
        self.pt_list.append(point)

    def add_id(self, id):
        '''Receives an id and adds it to the list of ids'''
        self.id_list.append(id)

    def draw_oval(self, canvas, point):
        """Draws an oval in a given point"""
        x, y = point
        # offset, got to be slightly lower than width/2 so it wont buldge out
        circle_off = self.width/2 - 1
        c_x1, c_y1 = (x - circle_off), (y - circle_off)
        c_x2, c_y2 = (x + circle_off), (y + circle_off)
        id = canvas.create_oval(c_x1, c_y1, c_x2, c_y2,
                                fill=self.color, outline="")
        self.id_list.append(id)

    def delete_from_canvas(self, canvas):
        '''Deletes the entire drawing from the canvas.'''
        for id_ in self.id_list:
            canvas.delete(id_)

        self.id_list = []

    def draw(self, canvas):
        '''
        draws the entire drawing
        '''

        if len(self.pt_list) == 1:  # Deals with the case of only one point in the drawing
            self.draw_oval(canvas, self.pt_list[0])
            return

        # converts the list of tuples to a list of the format [x,y,x,y,x,y,...]
        flattened = [a for x in self.pt_list for a in x]
        id_ = canvas.create_line(*flattened, width=self.width, fill=self.color)

        self.id_list.append(id_)

        if (self.width > 3):  # otherwise it looks weird
            self.draw_oval(canvas, self.pt_list[0])
            self.draw_oval(canvas, self.pt_list[-1])

    def draw_PIL(self, draw: ImageDraw.Draw):
        draw.line(self.pt_list, fill=self.color, width=self.width)
        for pt in self.pt_list:
            x, y = pt
            # offset, got to be slightly lower than width/2 so it wont buldge out
            circle_off = self.width/2 - 1
            c_x1, c_y1 = (x - circle_off), (y - circle_off)
            c_x2, c_y2 = (x + circle_off), (y + circle_off)
            id = draw.ellipse((c_x1, c_y1, c_x2, c_y2),
                              fill=self.color, outline=None)
            self.id_list.append(id)
