from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionNode, PandaNode, TextNode
from panda3d.core import CollisionSphere, CollisionPlane
from panda3d.core import Point3, Plane, Vec3
from panda3d.core import CollisionHandlerPusher, CollisionHandlerQueue, CollisionTraverser
from panda3d.core import KeyboardButton, BitMask32
from panda3d.core import WindowProperties
from panda3d.core import GeomVertexData, GeomVertexFormat, Geom, GeomTriangles, GeomVertexWriter, GeomNode
from direct.showbase import Audio3DManager

import simplepbr
from math import sin, cos, pi

#Things to ADD:
#Remaining Eggs (2/7)


class gameEngine(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        simplepbr.init()
        
        self.gravity = 10
        self.p_speed = 10
        self.camera_speed = 20
        self.last_time = 0
        self.lock = True
        self.jump_v = 0
        self.jump_h = 5
        self.score = 0
        self.egg_sounds = {}
        
        self.base_cam_x = 0
        self.base_cam_y = 0
        
        self.cam_y_pos = base.win.getYSize() // 2
        
        #magic numbers
        box_space = 400
        boundry_floor = 10
        boy_radius = 1
        self.dead_zone = 0.01
        
        
        
        self.props = WindowProperties()
        self.props.setCursorHidden(self.lock)
        base.win.requestProperties(self.props)
        
        #addCollision Traverser and handler
        traverser = CollisionTraverser()
        base.cTrav = traverser
        pusher = CollisionHandlerPusher()
        self.queue = CollisionHandlerQueue()
        
        #setup 3d Audio
        self.audio = Audio3DManager.Audio3DManager(base.sfxManagerList[0], camera)
        self.audio.setListenerVelocityAuto()
        
        #Add Gui
        scoreLabel = TextNode('scoreLabel')
        scoreLabel.setText("Score: ")
        scoreLabelPath = aspect2d.attachNewNode(scoreLabel)
        scoreLabelPath.setScale(0.07)
        scoreLabelPath.setPos(-1.25,0,0.93)
        
        self.scoreDisplay = TextNode('scoreDisplay')
        self.scoreDisplay.setText(str(self.score))
        scoreDisplayPath = aspect2d.attachNewNode(self.scoreDisplay)
        scoreDisplayPath.setScale(0.07)
        scoreDisplayPath.setPos(-1,0,0.93)
        
        #Setup Skybox        
        self.floor = self.generate_full_wall(box_space, box_space, 'floor', z=-boundry_floor, img='sky2.png')
        self.north_wall = self.generate_full_wall(box_space, box_space, 'n_wall', y=box_space/2, ry=90, img='sky.png')
        self.south_wall = self.generate_full_wall(box_space, box_space, 's_wall', y=-box_space/2, rx=90, rz=90, ry=90, img='sky.png')
        self.east_wall = self.generate_full_wall(box_space, box_space, 'e_wall', x=box_space/2, rz=-90, ry=90, img='sky.png')
        self.west_wall = self.generate_full_wall(box_space, box_space, 'w_wall', x=-box_space/2, rz=90, ry=90, img='sky.png')
        self.ceiling = self.generate_full_wall(box_space, box_space, 'ceiling', z=box_space/2, rz=180, img='sky2.png')
        
        
        #Load world
        scene = self.loader.loadModel('world.bam')
        
        eggs = scene.findAllMatches('**/=Egg')
        colliders = scene.findAllMatches('**/+CollisionNode')
        
        
        
        for collider in colliders:
            realNode = collider.parent
            for child in collider.children:
                child.reparentTo(realNode)
            collider.hide()
        
        # for collider in hide_list:
            # collider.hide()
            
        for egg in eggs:
            self.accept('playerCol-into-' + egg.name, self.collect_egg)
            self.egg_sounds[egg.name] = base.loader.loadSfx(egg.getTag('Egg') + '.mp3')
          
        #For some reason I need to store the model path in order to keep this working
        #Lol lmao
        self.sounds = []
        for speaker in scene.findAllMatches('**/=sound'):            
            mySound = self.audio.loadSfx(speaker.getTag('sound'))
            self.audio.attachSoundToObject(mySound, speaker)
            self.sounds.append(speaker)
            
            self.audio.setSoundVelocityAuto(mySound)
            mySound.setLoop(True)
            mySound.play()
        
        scene.reparentTo(self.render)
        
        #Load player
        player = PandaNode('player')
        self.playerPath = render.attachNewNode(player)
        
        playerColNode = CollisionNode('playerCol')
        body = CollisionSphere(0,0,0,boy_radius)
        legs = CollisionSphere(0,0,-2,boy_radius)
        playerColNode.addSolid(body)
        playerColNode.addSolid(legs)
        playerColNode.setFromCollideMask(BitMask32(0x01))
        playerColPath = self.playerPath.attachNewNode(playerColNode)
        playerColPath.setCollideMask(BitMask32(0x01))  
        
        playerColPath.show()
        
        feet = CollisionSphere(0,0,-3, boy_radius/2)
        feetColNode = CollisionNode('playerFeet')
        feetColNode.addSolid(feet)
        feetColNode.setFromCollideMask(BitMask32(0x02))
        feet.tangible = False
        playerFeet = self.playerPath.attachNewNode(feetColNode)
        playerFeet.setCollideMask(BitMask32(0x02))
        
        playerFeet.show()
        
        self.playerPath.setPos(5,5,5)

        pusher.addCollider(playerColPath, self.playerPath)
        traverser.addCollider(playerColPath, pusher)
        traverser.addCollider(playerFeet, self.queue)
        
        pusher.addInPattern('%fn-into-%in')

        #setup controls
        self.forward_button = KeyboardButton.ascii_key('w')
        self.backward_button = KeyboardButton.ascii_key('s')
        self.right_button = KeyboardButton.ascii_key('d')
        self.left_button = KeyboardButton.ascii_key('a')
        self.jump_button = KeyboardButton.space()
        self.shift = KeyboardButton.shift()
        
        self.accept('r', self.p_restart)
        
        #Camera setup
        self.camera.reparentTo(self.playerPath)
        base.disableMouse()        
        self.accept('escape', self.swich_lock)
        base.win.movePointer(0, int(base.win.getXSize() / 2), int(base.win.getYSize() / 2))
        self.camera.setPos(0,-boy_radius,0)

        #Setup frame_update
        taskMgr.add(self.frame_update, 'frame_update')
        
    def frame_update(self, task):
        ds = task.time - self.last_time
    
        is_down = base.mouseWatcherNode.is_button_down
    
        y_speed = 0
        if is_down(self.forward_button):
            y_speed += self.p_speed * ds
            
        if is_down(self.backward_button):
            y_speed -= self.p_speed * ds
            
        x_speed = 0
        if is_down(self.right_button):
            x_speed += self.p_speed * ds
            
        if is_down(self.left_button):
            x_speed -= self.p_speed * ds
            
        #z_speed = self.gravity * ds
        
        jump = False
        base.cTrav.traverse(render)
        for entry in self.queue.entries:
            jump = True
            
        if is_down(self.jump_button) and jump:
            self.jump_v = self.jump_h * 2
        else:
            self.jump_v -= self.gravity * ds
            
        if self.jump_v < -self.gravity:
            self.jump_v = -self.gravity
            
        z_speed = self.jump_v * ds
        
        camera_x = 0
        camera_y = 0
        if base.mouseWatcherNode.hasMouse():
            x = base.mouseWatcherNode.getMouseX() - self.base_cam_x
            y = base.mouseWatcherNode.getMouseY() - self.base_cam_y
            
            
            if x <= self.dead_zone and x >= -self.dead_zone:
                x = 0
            
            if y <= self.dead_zone and y >= -self.dead_zone:
                y = 0

            if self.lock:
                camera_x = -x * self.camera_speed
                camera_y = y * self.camera_speed
            
                base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)
    
        
        angle = (self.playerPath.getH() / 360) * 2 * pi
        

        actual_x = -(sin(angle) * y_speed)
        actual_y = cos(angle) * y_speed
        
        actual_x += cos(angle) * x_speed
        actual_y += sin(angle) * x_speed
        
        if is_down(self.shift):
            actual_x *= 2
            actual_y *= 2

        self.playerPath.setFluidPos(self.playerPath.getX() + actual_x, self.playerPath.getY() + actual_y, self.playerPath.getZ() + z_speed)
        self.playerPath.setHpr(self.playerPath.getH() + camera_x, self.playerPath.getP() + camera_y, self.playerPath.getR())

        self.last_time = task.time
        return task.cont
       
    #button events
    def swich_lock(self):
        if self.lock:
            self.lock = False
        else:
            self.lock = True
            
        self.props.setCursorHidden(self.lock)
        base.win.requestProperties(self.props)
    
    def p_restart(self, entry = None):
        self.playerPath.setPos(5,5,5)
    
    def collect_egg(self, entry):
        #print(entry)
        entry.getIntoNodePath().parent.removeNode()
        self.score += 1
        self.scoreDisplay.setText(str(self.score))
        self.egg_sounds[entry.getIntoNodePath().name].play()
        
        
    def generate_plane(self, width, height, name='plane'):
        # vdata = GeomVertexData('test', GeomVertexFormat.getV3n3cpt2(), Geom.UHStatic)
        # vdata.setNumRows(4)
        
        vdata = GeomVertexData('test', GeomVertexFormat.getV3n3t2(), Geom.UHStatic)
        vdata.setNumRows(4)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        #color = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        vertex.addData3(width/2, -(height/2), 0)
        normal.addData3(0, 0, 1)
        #color.addData4(0, 0, 1, 1)
        texcoord.addData2(1, 0)

        vertex.addData3(width/2, height/2, 0)
        normal.addData3(0, 0, 1)
        #color.addData4(0, 0, 1, 1)
        texcoord.addData2(1, 1)

        vertex.addData3(-(width/2), height/2, 0)
        normal.addData3(0, 0, 1)
        #color.addData4(0, 0, 1, 1)
        texcoord.addData2(0, 1)

        vertex.addData3(-(width/2), -(height/2), 0)
        normal.addData3(0, 0, 1)
        #color.addData4(0, 0, 1, 1)
        texcoord.addData2(0, 0)

        prim = GeomTriangles(Geom.UHStatic)
        prim.addVertices(0,1,2)
        prim.addVertices(2,3,0)

        geom = Geom(vdata)
        geom.addPrimitive(prim)

        node = GeomNode(name)
        node.addGeom(geom)
        nodePath = render.attachNewNode(node)
        return nodePath
        
    def create_wall(self, width, height, name='wall', x=0, y=0, z=0, rx=0,ry=0,rz=0, img='Untitled.png'):
        wall = self.generate_plane(width, height, name)
        wall.setHpr(rx,ry,rz)
        wall.setPos(x,y,z)
        
        tex = loader.loadTexture(img)
        #print(tex)
        wall.setTexture(tex)
        return wall
        
    def generate_full_wall(self, width, height, name='wall', x=0, y=0, z=0, rx=0,ry=0,rz=0, img = 'Untitled.png'):
        wall = self.create_wall(width, height, name, x, y, z, rx, ry, rz, img)
        collNode = CollisionNode(name)
        collNode.addSolid(CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0))))
        collPath = wall.attachNewNode(collNode)
        
        self.accept('playerCol-into-' + name, self.p_restart)
        
        
        return collPath
game = gameEngine()
game.run()