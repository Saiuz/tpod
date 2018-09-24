
# Copyright 2018 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# return is t -> (vx, vy)
def velocityforboxes(boxes):
    frametobox = {box.frame: box for box in boxes} 
    times = sorted(frametobox.keys())
    vels = {}
    for i, time in enumerate(times):
        last = times[max(0, i - 3)]
        nxt = times[min(len(times)-1, i + 3)]
        delta = nxt - last
        if frametobox[time].lost == 0 or delta == 0:
            velx = 0
            vely = 0
        else:

            velx = float(frametobox[nxt].xbr - frametobox[last].xbr) / float(delta)
            vely = float(frametobox[nxt].ybr - frametobox[last].ybr) / float(delta)
        vels[time] = (velx, vely)
    return vels
 
