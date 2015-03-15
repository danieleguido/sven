'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # concepts
 */
angular.module('svenClientApp')
  .directive('concepts', function () {
    return {
      template: '<div class="mouse tooltip">...</div><div class="viewer"></div>',
      restrict: 'E',
      
      scope: {
        data: '=',
        measure: '=',
        groups: '=',
        bounds: '=',
        toggle: '&'
      },
      link: function postLink(scope, element, attrs) {
        var tooltip = d3.select("div.tooltip.mouse"),
            matrix   = snark
              .matrix()
              .init(d3.select(".viewer")),
            previous_concept = {},
            previous_group = {};

        var get_tooltip = function(concept_id, group_id) {
          var t = function(concept, group) {
            
            if(group){
              var groupmeasures = concept.cols.filter(function(d){
                return d.G == group.name
              })[0];
              
              return [
                '<h4>"',concept.segment__cluster, '" in ', group.name, '</h4>',
                '<div class="tooltip-measures">tf ..... ',
                groupmeasures?(Math.round(+groupmeasures.tf * 10000)/10000): 0,
                '<br/>tfidf .. ',
                groupmeasures?(Math.round(+groupmeasures.tf_idf * 10000)/10000):0,
                groupmeasures?'':'<br/>distr .. absent',
                  '</div>'
              ].join('');
            }
            return [
              '<h4>',
              concept.segment__cluster,
              
              '</h4><div class="tooltip-measures">tf ..... ',
              (Math.round(+concept.tf * 10000)/10000),
              '<br/>tfidf .. ',
              (Math.round(+concept.tf_idf * 10000)/10000),
              '<br/>distr .. ',
              +concept.distribution,
              '</div>'
            ].join('');

          };
          
          if(!group_id) {
            previous_group = null;
          } else if(previous_group && previous_group.name == group_id) {
            //
          } else {
            for(var i=0; i < scope.groups.length; i++) {
              if(scope.groups[i].name == group_id) {
                previous_group = scope.groups[i];
                break;
              }
            }
          }


          if(previous_concept && previous_concept.segment__cluster == concept_id) {
            return t(previous_concept, previous_group);
          };
          
          try{
            previous_concept = scope.data.filter(function(d){
              return d.segment__cluster==concept_id
            })[0];
          } catch(e){
            console.log("tooltip not found for concept id", concept_id);
            return '';
          }

          return t(previous_concept,previous_group)
        };


        $('.viewer').on('scroll', function(e){
          matrix.onscroll({
            left: $(this).scrollLeft()
          });
        }).on("mouseenter", ".block", function() {
          if(!scope.data) return;

          tooltip
            .text('')
            .style("opacity", 1)
          
        }).on("mousemove", ".block", function(event) {
          var concept   = $(this),
              concept_id = concept.attr('cid'),
              group_id   = $(event.target).attr('gid'),
              text = get_tooltip(concept_id, group_id);

          tooltip
            .style("opacity", 1)
            .style("left", Math.max(0, event.pageX - 200) +  "px")
            .style("top", (event.pageY - 10) + "px")
            .html(text);

        }).on("mouseleave",  ".block", function() {

          tooltip
            .style("opacity", 0)

        }).on("click", "circle.toggler", function(){

          var concept   = $(this),
              concept_id = concept.attr('cid');

          scope.toggle({concept_id: concept_id});

        });

        var render = function() {
          // get positions for each set
          
          if(scope.data && scope.groups && scope.bounds)
            matrix
              .headers(scope.groups)
              .data(scope.data, function(d) {return d.segment__cluster;})
              .update({ bounds: scope.bounds, measure:scope.measure||'tf'})
          
        }



        scope.$watch('data', render, true);

        scope.$watch('measure', render, true);
      }
    };
  });
