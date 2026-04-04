import moderngl as mgl
import numpy as np
import pygame as pg
import cProfile
import struct



def modernGltest():
    '''creates a context for the current window/screen made 
    by pygame then fills the buffer with the bytes for hello word, 
    then reads them and returns the context'''

    ctx = mgl.get_context()
    buf = ctx.buffer(b"Hello World!")
    print(buf.read())
    return ctx


def createVertexShader(ctx):
    '''creates the vertex shader/program for the context, this version will square each input'''

    return ctx.program(
        vertex_shader="""
        #version 330

        in float num1;
        in float num2;

        out vec2 value;
        out float product;

        void main() {
            value = vec2(float(num1), float(num2));
            product = float(num1 * num2);
        }
        """,
        varyings=["value", "product"],
    )


def runVertexShading(ctx, program, vertexCount = 10):
    '''sets the vao to be an empty vertex array, (gl_VertexID) instead of a passed buffer of vertexs.
    reserves vertexCount * 8 bytes in the buffer, since each vertex outs 2 floats at 4 bytes each. 
    then transforms the vao, which runs the vertex shader a total of (vertexCount) times and stores 

    the output in the buffer.'''
    
    evilverticies = [1,2,3,4,5,1.2,1.3,1.4]

    vertexArray = np.array(evilverticies, dtype="f4")
    vertexBuffer = ctx.buffer(vertexArray.tobytes())

    vertexCount = len(evilverticies) // 2

    vao = ctx.vertex_array(program, vertexBuffer,  "num1", "num2")

    buffer = ctx.buffer(reserve=vertexCount * 12)
    # 3 floats per vertex out, 4 bytes each
    
    vao.transform(buffer, vertices=vertexCount)
    # ^ this calls the buffer to actually do the math

    data = struct.unpack(f"{vertexCount * 3}f", buffer.read())
    print(data)

    for i in range(0, vertexCount * 3, 3):

        print("input = {}, product = ({})".format(data[i:i + 2], data[i + 2]))
        print(i)
        print(data[i])







def main():
    pg.init()
    pg.font.init()

    ######## settings pay attention to me ##############

    windowHeight = 700
    windowWidth = 700

    backGroundColor = (0, 0, 0)

    ####################################################


    ################ Setup stuff #######################
    screenCenterX = windowWidth / 2
    screenCenterY = windowHeight / 2

    # pg definitions
    pg.display.set_mode((windowWidth, windowHeight), pg.OPENGL | pg.DOUBLEBUF)
    myFont = pg.font.Font(None, 50)
    clock = pg.time.Clock()
    running = True

    ####################################################


    ctx = modernGltest()
    program = createVertexShader(ctx)
    runVertexShading(ctx, program)




    ############# Window Loop ################

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
        ctx.clear(
            backGroundColor[0] / 255,
            backGroundColor[1] / 255,
            backGroundColor[2] / 255,
            1.0
        )
        pg.display.flip()
        clock.tick(60)
    pg.font.quit()
    pg.quit()

    ##########################################


main()