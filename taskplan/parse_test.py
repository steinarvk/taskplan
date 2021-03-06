from .parse import *


def test_parse_house():
    parse_yaml_to_plannable_tasks(
        """
workers:
- name: alice
  group: architect
- name: bob
  group: builder
- name: charlie
  group: builder, carpenter
- name: cindy
  group: client
- name: david
  group: designer
- name: elaine
  group: electrician
- name: frank
  group: finance
- name: mindy
  group: moving
- name: peter
  group: plumber
tasks:
- name: sketch-requirements
  worker: cindy
  duration: 3
- name: draw-house
  worker: architect
  duration: 10
  milestone: plans-ready
  requires:
  - sketch-requirements
- name: estimate-building-costs
  milestone: costs-ready
  duration: 10
  worker: builder
  requires: draw-house
- name: estimate-electrical-costs
  milestone: costs-ready
  duration: 4
  worker: electrician
  requires: draw-house
- name: estimate-moving-costs
  milestone: costs-ready
  duration: 4
  worker: moving
  requires: draw-house
- name: estimate-plumbing-costs
  milestone: costs-ready
  duration: 4
  worker: plumber
  requires: draw-house
- name: estimate-design-costs
  milestone: costs-ready
  duration: 4
  worker: designer
  requires: draw-house
- name: estimate-carpentry-costs
  milestone: costs-ready
  duration: 10
  worker: carpenter
  requires: draw-house
- name: verify-budget
  duration: 4
  worker: finance
  milestone: greenlight-project
  requires: costs-ready
- name: lay-foundation
  worker: builder
  duration: 5
  requires: greenlight-project
- name: build-scaffolding
  worker: builder
  duration: 5
  requires: lay-foundation
- name: build-load-bearing-walls
  worker: builder
  milestone: build-walls, outer-house-ready
  duration: 10
  requires: build-scaffolding
- name: build-other-walls
  worker: builder
  milestone: build-walls, outer-house-ready
  duration: 10
  requires: build-scaffolding
- name: build-roof
  worker: builder
  milestone: outer-house-ready
  requires: build-load-bearing-walls
  duration: 5
- name: design-interior
  worker: designer
  duration: 5
  requires: draw-house, greenlight-project
- name: greenlight-interior
  worker: client
  duration: 7
  requires: design-interior
- name: order-furniture
  worker: [designer, client, finance]
  duration: 5
  milestone: furniture-ready
  requires: greenlight-interior
- name: build-custom-furniture
  worker: carpenter
  milestone: furniture-ready
  duration: 10
  requires: greenlight-interior
- name: install-furniture
  worker: [builder, moving]
  duration: 3
  milestone: house-ready
  requires:
  - furniture-ready
  - build-walls
- name: build-floors
  worker: builder
  duration: 10
  requires: build-scaffolding
- name: install-plumbing
  worker: plumber
  duration: 5
  milestone: house-ready
  requires: outer-house-ready
- name: install-electricity
  worker: electrician
  duration: 5
  milestone: house-ready
  requires: outer-house-ready
- name: verify-sound-construction
  worker: architect
  duration: 4
  milestone: house-ready
  requires: build-roof, build-load-bearing-walls, build-floors
- name: move-personal-belongings
  worker: moving
  duration: 2
  milestone: all-done
  requires: house-ready
"""
    )
