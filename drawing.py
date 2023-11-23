class Drawing:
    def __init__(self, canvas, color, width, pt_list=[], id=-1):
        self.pt_list = pt_list.copy()
        self.id_list = []
        
        self.id = id # id of the whole drawing in the sql db, not an id of a stroke on the canvas
        
        self.canvas = canvas
        self.color = color
        self.width = width

    
    def add_point(self, point):
        '''
        recives a point as a tuple and the id of the point in the tk canvas and adds then to their lists
        '''
        self.pt_list.append(point)

    def add_id(self, id):
        self.id_list.append(id)
    
    def draw_oval(self, point):
        x, y = point
        circle_off = self.width/2 - 1 #offset, got to be slightly lower than width/2 so it wont buldge out
        c_x1, c_y1 = (x - circle_off), (y - circle_off)
        c_x2, c_y2 = (x + circle_off), (y + circle_off)
        id = self.canvas.create_oval(c_x1, c_y1, c_x2, c_y2, fill=self.color, outline="")
        self.id_list.append(id)
    
    def delete_from_canvas(self):
        for id in self.id_list:
            self.canvas.delete(id)
        
        self.id_list = []

    def draw_drawing(self):
        '''
        draws the entire drawing
        '''
        # for i in range(len(self.pt_list) - 1):
        #     x1, y1 = self.pt_list[i]
        #     x2, y2 = self.pt_list[i+1]

        #     id = self.canvas.create_line(x1, y1, x2, y2, fill=self.color, width=self.width)
        #     self.id_list.append(id)
            
        #     if (self.width > 3): # otherwise it looks weird
        #         self.draw_oval((x1, y1))
        
        # self.draw_oval(self.pt_list[-1])
        
        if len(self.pt_list) == 1: #Deals with the case of only one point in the drawing
            self.draw_oval(self.pt_list[0])
            return
        

        flattened = [a for x in self.pt_list for a in x] # converts the list of tuples to a list of the format [x,y,x,y,x,y,...]
        id = self.canvas.create_line(*flattened, width=self.width, fill=self.color)

        self.id_list.append(id)

        if (self.width > 3): # otherwise it looks weird
            self.draw_oval(self.pt_list[0])
            self.draw_oval(self.pt_list[-1])


if __name__ == "__main__":
    d = Drawing()
    d.add_point_and_id((5,3))