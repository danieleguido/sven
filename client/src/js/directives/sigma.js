'use strict';

/*
  Sigma addons
  ---
  thanks to @jacomyal (it need to be added before creating any new instance)
*/
sigma.classes.graph.addMethod('neighbors', function (nodeId) {
  var k,
      neighbors = {},
      index     = this.allNeighborsIndex[nodeId] || {};

  for (k in index)
    neighbors[k] = this.nodesIndex[k];
  neighbors[nodeId] = this.nodesIndex[nodeId];
  return neighbors;
});

/**
 * @ngdoc overview
 * @name sven
 * @description
 * # sven
 *
 * directive to show a grapgh of nodes and edges thanks to @Yomguithereal!!! 
 */
angular.module('sven')
  .directive('gmasp', function ($log, $location) {
    return {
      restrict : 'A',
      template: ''+ 
        '<div class="gasp {{enabled?\'enabled\':\'disabled\'}}"><div class="inner {{target.type||\'\'}}">'+ 
          '<span class="text" ng-if="target.type == \'document\'" ><i>selected</i>: ' + 
            '<a href="{{href}}">{{label}}<a>' + 
          '</span>' + 
          '<span class="text" ng-if="target.type == \'segments__cluster\'" ><i>concept</i>&nbsp;' + 
            '<b ng-click="applyFilter()">{{label}}<b>' + 
          '</span>' + 
          '<span class="text" ng-if="target.type == \'tags__slug\'" ><i>tag</i>&nbsp;' + 
            '<b ng-click="applyFilter()">{{label}}<b>' + 
          '</span>' + 
          '<span class="text" ng-if="target.type == \'edge\'">'+
            '<i class="fa fa-circle {{left.type}}"></i> &#8594; <i class="fa fa-circle {{right.type}}"></i> {{left.label}} &#8594; ' +
            '{{right.label}} </span>' + 
          // '<div class="action-group">'+
          //   '<a class="action slide {{target.type == \'node\'? \'enabled\': \'disabled\'}}" href="{{href}}" title="visit" data-action="link" tooltip="{{linkto}}">'+
          //     '<span class="fa fa-link"></span></a>'+
          //   '<a class="action queue" tooltip="add to your current playlist" data-action="queue">'+
          //     '<span class="fa fa-play-circle-o"></span></a>' +
            
          // '</div>' +
        '</div></div>',
      scope:{
        target : '='
      },
      link : function(scope, element, attrs) {
        var _gasp = $(element[0]); // gasp instance;
        scope.enabled = false;
        $log.log('::gmasp ready');
        
        scope.applyFilter = function () {
          $log.log('::gmasp applyFilter()');
          scope.$parent.changefilters({
            key: scope.target.type,
            value: scope.target.data.node.id
          })
        }

        // enable / disable gasp instance
        scope.$watch('target', function(v) {
          $log.log('::gmasp @target - value:', v);
          if(!v || !v.type) {
            // make it NOT visible
            scope.enabled = false;
            return;
          }
          // handle label according to target type (node or edge)
          if(v.type=='document') {
            scope.href  = '#/document/' + v.data.node.id;
            scope.label = v.data.node.label;
            scope.type = v.data.node.type;
          } else if(v.type=='segments__cluster'){
            scope.label = v.data.node.label;
            scope.filter = {
              key: v.data.node.type,
              value: v.data.node.cluster
            }
          } else if(v.type=='tags__slug') {
            scope.label = v.data.node.label;
            scope.filter = {
              key: v.data.node.type,
              value: v.data.node.id
            }
          }
          // make it visible
          scope.enabled = true;
          
        })
      }
    }
  })

  .directive('sigma', function($log, $location) {
    return {
      restrict : 'A',
      template: ''+
        '<div id="playground"></div>' +
        '<div gmasp target="target"></div>' + 
        '<div id="tips" ng-if="tips.length > 0"><div>{{tips}}</div></div>' +
        '<div id="commands" class="{{isNeighborhoodVisible?\'lookup\':\'\'}}">' +
          '<div tooltip-placement="left" tooltip="view all nodes" tooltip-append-to-body="true" class="action {{isNeighborhoodVisible? \'bounceIn animated\': \'bounceOut animated\'}}" ng-click="toggleLookup()"><i class="fa fa-eye"></i></div>' +
          
          '<div tooltip-placement="left" tooltip="play/stop layout algorithm" tooltip-append-to-body="true"  class="action {{status==\'RUNNING\'? \'bounceIn animated\': \'\'}}" ng-click="togglePlay()"><i class="fa fa-{{status==\'RUNNING\' ? \'stop\': \'play\'}}"></i></div>' +
          '<div tooltip-placement="left" tooltip="zoom back to the whole network" tooltip-append-to-body="true"  class="action" ng-click="rescale()"><i class="fa fa-dot-circle-o"></i></div>' +
          '<div tooltip-placement="left" tooltip="zoom in" tooltip-append-to-body="true" class="action" ng-click="zoomin()"><i class="fa fa-plus"></i></div>' +
          '<div tooltip-placement="left" tooltip="zoom out" tooltip-append-to-body="true" class="action" ng-click="zoomout()"><i class="fa fa-minus"></i></div>' +
        '</div>',
      scope:{
        graph: '=',
        tips: '=',
        controller: '=',
        measure: '=', // node property name to be used in order to size the nodes
        redirect: '&',
        toggleMenu: '&togglemenu',
        changefilters: '&'
      },
      link : function(scope, element, attrs) {

        scope.target = {};

        // Creating sigma instance
        var timeout,
            
            tooltip = {
              tip: $("#tooltip-sigma"),
              el: $("#tooltip-sigma-label"),
              isVisible: false,
              text: ''
            },

            IS_RUNNING     = 'RUNNING',
            IS_STOPPED     = 'STOPPED',
        
            layoutDuration    = 10000, // 10 sec default
            minlayoutDuration = 4500,
            maxlayoutDuration = 25000, 
            doNotDisplayEdges = false,
            

            labels = {
              nodes: {},
              sorting: [], 
            }, // the collection of labels to be visualized one after the other (according to node position, from top to left)
            si = new sigma({
                settings: {
                  singleHover: true,
                  labelThreshold: 0,
                  labelSizeRatio: 3.5,
                  // labelSize: 'fixed',
                  defaultLabelSize: '12',
                  labelHoverShadowColor: '#a5a5a5',
                  labelHoverShadowBlur: 16,
                  labelSize: ''
                }
              }),
            camera = si.addCamera('main'),
            
            colors = {
                'person': "rgba(33, 33, 33, 0.7)",
                'collection': '#16cc00',
                'resource': '#cc1600',
                'resourceKnown': '#cc1600'
              },
            
            timers = {
                play: 0
              },
            
            scale = d3.scale.linear()
              .domain([0,100])
              .range(['#d4d4d4', '#909090']);
        
        
        
        // set theinitial status
        scope.status = IS_STOPPED;
        scope.isNeighborhoodVisible = false;
        
        // create the main camera and specify 'canvas'
        si.addRenderer({
          type: 'canvas',//canvas',
          camera: 'main',
          container: element.find('#playground')[0]
        });
        
        
        /*
          
          Scope watchers
          ---
        
        */
        /*
          Watch: current controller
          if the current controller needs a bit more horizontal space,
          sigma instance needs to refresh to adapt to its parent new size;
          (that is, the class 'extended' ahs been added to the element)
        */
        scope.$watch('controller', function (ctrl) {
          $log.log('::sigma @controller changed');
          setTimeout(function() {
            $log.log('::sigma @controller changed -> rescale()');
            rescale();
            si.refresh();
          }, 300);
        });
        
        scope.$watch('freeze', function (v) {
          if(v=='sigma')
            stop();
        });
        // whenever nodesize changes, check that the graph exists, then resize nodes according to nodesize property name
        scope.$watch('measure', function (v) {
          $log.log('::sigma @measure changed', v);
          if(si.graph.nodes().length == 0)
            return;

          stop();
          si.graph.nodes().forEach(function (n) {
            if(v == 'degree')
              n.size = Math.sqrt(si.graph.degree(n.id)) * 2;
            else
              n.size = n[v] || 1
          });
          si.refresh();
          play();
        });

        
        /*
          Watch: current graph
          Redraw the current graph, calculate the force layout min duration
        */
        scope.$watch('graph', function (graph, previousGraph) {
          $log.log('::sigma @graph changed');
          stop();
          clearTimeout(timers.play);
          
          if(!graph || !graph.nodes || !graph.nodes.length) {
            $log.log('::sigma @graph empty, clear...');
            // clean graph, the exit
             si.graph.clear();
             si.refresh();
            return;
          }
            
          
          // refresh the scale for edge color, calculated the extent weights of the edges
          scale.domain(d3.extent(graph.edges, function(d) {return d.weight || 1}));
          
          // Reading new graph
          si.graph.clear().read(graph);
          
          // exit
          if(si.graph.nodes().length == 0)
            return;
          // calculate a default duration 
          layoutDuration = Math.max(Math.min(4* si.graph.nodes().length * si.graph.edges().length, maxlayoutDuration),minlayoutDuration)
          $log.log('::sigma n. nodes', si.graph.nodes().length, ' n. edges', si.graph.edges().length, 'runninn layout atlas for', layoutDuration/1000, 'seconds')
          
          si.graph.edges().forEach(function (e) {
            e.size = e.weight;
          })
          si.graph.nodes().forEach(function (n) {
            // console.log(n)
            n.label = n.label || n.name;
            n.color = colors[n.type] || "#353535";
            n.x = n.x || Math.random()*50
            n.y = n.y || Math.random()*50
            n.size = n[scope.measure] ||  1;
          });
          if(graph.nodes.length > 50) {
            si.settings('labelThreshold', 3.5);
            si.settings('labelSize', 'fixed');
            $log.log('::sigma change settings, a lot of nodes')
          } else {
            
            si.settings('labelThreshold', 0);
            si.settings('labelSize', 'fixed');
          }
          
          doNotDisplayEdges = si.graph.edges().length > 500;

          //if(!previousGraph)
            
          $log.log('::sigma force atlas starting in .35s')
          timers.play = setTimeout(function(){
            rescale();
            si.refresh();
            play();
            scope.status = IS_RUNNING
            scope.$apply() 
          }, 150)
          
        });
        
         /*
        
          Software takes command ...
          ---
        
        */
        scope.togglePlay = function() {
          $log.log('::sigma -> togglePlay', scope.status);
          if(scope.status == IS_RUNNING) {
            stop();
          } else {
            play();
          }
        }
        
        /*
        
          DOM liteners
          ---
        
        */
        /*
          DOM click [data-id]
          check for focus changes
        */
        $(document).on('click', '[data-id]', focus);
        // $(document).on('mouseenter', '[data-id]', function(e) {
          
        // });
        // deprecaded, we do not understand what happens $(document).on('mouseenter', '[data-id]', focus);
        /*
          sigma clickNode
          @todo
        */
        // si.bind('')
        si.bind('clickNode', function(e){
          stop();
          $log.log('::sigma @clickNode', e.data.node.id,e.data.captor, e.data.node.type || 'entity', e.data.node.label);
          
          // trigger to jquery (better via angular, @todo)
          $('body').trigger('sigma.clickNode', {
            type: e.data.node.type,
            id: e.data.node.id,
            captor: e.data.captor
          })

          // calculate the node do keep
          var toKeep = si.graph.neighbors(e.data.node.id);
           
          // enlighten the egonetwork
          si.graph.nodes().forEach(function (n) {
            n.discard = !toKeep[n.id];
          });
          si.graph.edges().forEach(function (e) {
            e.discard = !(toKeep[e.source] && toKeep[e.target])
          });

          // add the link (or provide the filter, if it is enabled)
          scope.target = {
            data: e.data,
            type: e.data.node.type
          };
          scope.isNeighborhoodVisible = true;
          scope.$apply();

          si.refresh();
          
        });
        

        /*
          listener overNode
          on mouseover, draw the related tooltip in the correct position.
          We use the renderer since the tooltip is relqtive to sigma parent element.
        */
        si.bind('overNode', function(e) {
          // console.log(e.data.node, tooltip.el)
          if(tooltip.timer)
            clearTimeout(tooltip.timer);
          console.log(e)
          tooltip.tip.css({
            top: e.data.captor.clientY, //e.data.node['renderer1:y'],
            left: e.data.captor.clientX// e.data.node['renderer1:x']
          });

          if(tooltip.text != e.data.node.name)
            tooltip.el.text(e.data.node.name);
          if(!tooltip.isVisible) {
            tooltip.el.css({
              opacity: 1
            });

          }
          tooltip.isVisible = true;

        });

        /*
          listener outNode
        */
        si.bind('outNode', function(e) {
          if(!tooltip.isVisible)
            return;
          if(tooltip.timer)
            clearTimeout(tooltip.timer);
          tooltip.timer = setTimeout(function() {
            tooltip.el.css({
              opacity: 0
            });
          }, 210);
          
          tooltip.isVisible = false;
        })

        
        si.bind('clickStage', function(e) {
          $('body').trigger('sigma.clickStage');
        })
        
        /*
        
          canvas / sigma js helpers
          ---
        
        */
        /*
          sigma focus
          Center the camera on focusId and enlighten the
          node
        */
        function focus(nodeId) {
          $log.info('::sigma --> focus()', nodeId)
          if(typeof nodeId == 'object') { // it is an event ideed
            
            nodeId = $(this).attr('data-id');
          }
          
          var node = si.graph.nodes(nodeId);
          try{
            sigma.misc.animation.camera(
              si.cameras.main,
              {
                x: node['read_cammain:x'],
                y: node['read_cammain:y'],
                ratio: 0.5
              },
              {duration: 250}
            );
          } catch(e) {
            
          }
        }
        /*
          sigma rescale
          start the force atlas layout
        */
        // once the container has benn added, add the commands. Rescale functions, with easing.
        function rescale() {
          sigma.misc.animation.camera(
            si.cameras.main,
            {x: 0, y: 0, angle: 0, ratio: 1.618},
            {duration: 150}
          );
        };
        
        /*
          sigma reset neighbors
          from egonetwork to other stories
        */
        function toggleLookup() {
          $log.debug('::sigma -> toggleLookup()')
          si.graph.nodes().forEach(function (n) {
            n.discard = false;
          });
          si.graph.edges().forEach(function (e) {
            e.discard = false
          });
          scope.isNeighborhoodVisible = false;
          // refresh the view
          // rescale()
          si.refresh();
        }
        /*
          sigma play
          start the force atlas layout
        */
        function play() {
          clearTimeout(timeout);
          timeout = setTimeout(function() {
            stop();
            scope.$apply(); // outside of the scope
          }, layoutDuration);
          
          scope.status = IS_RUNNING;
          
          si.startForceAtlas2({
            adjustSizes :true,
            linLogMode: true,
            startingIterations : 10,
            gravity : 1,
            edgeWeightInfluence : 10
          });
          $log.debug('::sigma -> play()')
        }
        /*
          sigma stop
          stop the force atlas layout
        */
        function stop() {
          clearTimeout(timeout);
          scope.status = IS_STOPPED;
          
          si.killForceAtlas2();
          $log.debug('::sigma -> stop()')
        }
        function zoomin() {
          sigma.misc.animation.camera(
            camera,
            {ratio: camera.ratio / 1.5},
            {duration: 150}
          );
        };
        function zoomout() {
          sigma.misc.animation.camera(
            camera,
            {ratio: camera.ratio * 1.5},
            {duration: 150}
          );
        };
        scope.rescale      = rescale; 
        scope.zoomin       = zoomin; 
        scope.zoomout      = zoomout;
        scope.toggleLookup = toggleLookup;
        /*
          sigma canvas drawNode
          given a canvas ctx, a node and sigma settings, draw the basic shape for a node.
        */
        function drawNode(node, context, settings, options) {
          var prefix = settings('prefix') || '';
          
          context.fillStyle = node.discard? "rgba(0,0,0, .11)": node.color;
        
          context.beginPath();
          context.arc(
            node[prefix + 'x'],
            node[prefix + 'y'],
            node[prefix + 'size'],
            0,
            Math.PI * 2,
            true
          );
          
          context.fill();
          context.closePath();
          
          // adding the small point
          // context.fillStyle = node.color;
          // context.beginPath();
          // context.arc(
          //   node[prefix + 'x'],
          //   node[prefix + 'y'],
          //   node[prefix + 'size'] - 1,
          //   0,
          //   Math.PI * 2,
          //   true
          // );
          // context.fill();
          // context.closePath();
          if( node[prefix + 'size'] > 3) {
            context.fillStyle = "#fff";
            context.beginPath();
            context.arc(
              node[prefix + 'x'],
              node[prefix + 'y'],
              1,
              0,
              Math.PI * 2,
              true
            );
            context.fill();
            context.closePath();
          }
        };
        
        
        /*
        
          Sigma type specific Renderers
          ---
        */
        sigma.canvas.nodes.personKnown = 
        sigma.canvas.nodes.resourceKnown =
        sigma.canvas.nodes.resource =
        sigma.canvas.nodes.def = function(node, context, settings) {
          drawNode(node, context, settings)
        };
        
        // sigma.canvas.nodes.personKnown = 
        // sigma.canvas.nodes.resourceKnown = function(node, context, settings) {
        //   var prefix = settings('prefix') || '';
        //   drawNode(node, context, settings);
        //   // Adding a border
          
        //   context.beginPath();
        //   context.setLineDash([3]);
        //   context.arc(
        //     node[prefix + 'x'],
        //     node[prefix + 'y'],
        //     node[prefix + 'size'] + 3,
        //     0,
        //     Math.PI * 2,
        //     true
        //   );

        //   context.closePath();
            
        //   context.lineWidth = node.borderWidth || 1;
        //   context.strokeStyle = node.borderColor || '#444';
        //   context.stroke();
          
          
        // };
        /*
          sigma canvas edge renderer
          
        */
        sigma.canvas.edges.def = function(edge, source, target, context, settings) {
          if(edge.discard)
            return;
          if(!scope.isNeighborhoodVisible && doNotDisplayEdges)
            return;
          var color = "#d4d4d4",
              prefix = settings('prefix') || '';

          if(edge.weight == 0)
            return;

          context.strokeStyle = edge.discard? '#d4d4d4' : scale(edge.weight||1)//color;
          context.lineWidth = 1//edge.discard? 1: 2;//edge[prefix + 'weight'] || edge.weight || 1;
          context.beginPath();
          context.moveTo(
            source[prefix + 'x'],
            source[prefix + 'y']
          );
          context.lineTo(
            target[prefix + 'x'],
            target[prefix + 'y']
          );
          context.stroke();
        };
        /*
          sigma canvas labels renderer
          
        */
        sigma.canvas.labels.def = function(node, context, settings) {
          var fontSize,
              prefix = settings('prefix') || '',
              size = node[prefix + 'size'];
          
          if(node.discard)
            return;
          
          if (size < settings('labelThreshold') && !scope.isNeighborhoodVisible)
            return;

          if (!node.label || typeof node.label !== 'string')
            return;
          
          if(node['renderer1:x'] < 0 || node['renderer1:y'] < 0)
            return;
          
          if(scope.isNeighborhoodVisible) {
            fontSize = settings('defaultLabelSize')
          } else {
            fontSize = (settings('labelSize') === 'fixed') ?
              settings('defaultLabelSize') :
              settings('labelSizeRatio') * size;
          }

          context.font = (settings('fontStyle') ? settings('fontStyle') + ' ' : '') +
            fontSize + 'px ' + settings('font');
          context.fillStyle = (settings('labelColor') === 'node') ?
            (node.color || settings('defaultNodeColor')) :
            settings('defaultLabelColor');

          context.fillText(
            node.label,
            Math.round(node[prefix + 'x'] + size + 3),
            Math.round(node[prefix + 'y'] + fontSize / 3)
          );
        };
        /*
          sigma canvas labels HOVER renderer
          
        */
        sigma.canvas.hovers.def = function(node, context, settings) {
          // console.log('hehe', context)
          var prefix = settings('prefix') || '';
          
          context.fillStyle = node.discard? "rgba(0,0,0, .21)": "rgba(255,255,255, .81)";
        
          context.beginPath();
          context.arc(
            node[prefix + 'x'],
            node[prefix + 'y'],
            node[prefix + 'size']+3,
            0,
            Math.PI * 2,
            true
          );
          
          context.fill();
          context.closePath();
          
          if( node[prefix + 'size']) {
            context.fillStyle = "#151515";
            context.beginPath();
            context.arc(
              node[prefix + 'x'],
              node[prefix + 'y'],
              3,
              0,
              Math.PI * 2,
              true
            );
            context.fill();
            context.closePath();
          }
          return;
          var x,
              y,
              w,
              h,
              e,
              fontStyle = settings('hoverFontStyle') || settings('fontStyle'),
              prefix = settings('prefix') || '',
              size = node[prefix + 'size'],
              fontSize = (settings('labelSize') === 'fixed') ?
                settings('defaultLabelSize') :
                settings('labelSizeRatio') * size;
          
          // Label background:
          context.font = (fontStyle ? fontStyle + ' ' : '') +
            fontSize + 'px ' + (settings('hoverFont') || settings('font'));
          
          context.beginPath();
          context.fillStyle = settings('labelHoverBGColor') === 'node' ?
            (node.color || settings('defaultNodeColor')) :
            settings('defaultHoverLabelBGColor');

          if (node.label && settings('labelHoverShadow')) {
            context.shadowOffsetX = 0;
            context.shadowOffsetY = 2;
            context.shadowBlur = settings('labelHoverShadowBlur') || 8;
            context.shadowColor = settings('labelHoverShadowColor');
          }

          if (node.label && typeof node.label === 'string') {
            x = Math.round(node[prefix + 'x'] - fontSize / 2 - 2);
            y = Math.round(node[prefix + 'y'] - fontSize / 2 - 2);
            w = Math.round(
              context.measureText(node.label).width + fontSize / 2 + size + 7
            );
            h = Math.round(+fontSize + 4);
            e = Math.round(fontSize / 2 + 2);

            context.moveTo(x, y + e);
            context.arcTo(x, y, x + e, y, e);
            context.lineTo(x + w, y);
            context.lineTo(x + w, y + h);
            context.lineTo(x + e, y + h);
            context.arcTo(x, y + h, x, y + h - e, e);
            context.lineTo(x, y + e);

            context.closePath();
            context.fill();

            context.shadowOffsetX = 0;
            context.shadowOffsetY = 0;
            context.shadowBlur = 0;
          }

          // Node border:
          if (settings('borderSize') > 0) {
            context.beginPath();
            context.fillStyle = settings('nodeBorderColor') === 'node' ?
              (node.color || settings('defaultNodeColor')) :
              settings('defaultNodeBorderColor');
            context.arc(
              node[prefix + 'x'],
              node[prefix + 'y'],
              size + settings('borderSize'),
              0,
              Math.PI * 2,
              true
            );
            context.closePath();
            context.fill();
          }

          // Node:
          var nodeRenderer = sigma.canvas.nodes[node.type] || sigma.canvas.nodes.def;
          nodeRenderer(node, context, settings);

          // Display the label:
          if (node.label && typeof node.label === 'string') {
            context.fillStyle = (settings('labelHoverColor') === 'node') ?
              (node.color || settings('defaultNodeColor')) :
              settings('defaultLabelHoverColor');

            context.fillText(
              node.label,
              Math.round(node[prefix + 'x'] + size + 3),
              Math.round(node[prefix + 'y'] + fontSize / 3)
            );
          }
        };
      }
    }
  });