'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:vimeo
 * @description
 * # vimeo
 */
angular.module('svenClientApp')
  .directive('vimeo', function () {
    return {
      template: '<div></div>',
      restrict: 'E',
      scope:{
        videoid:'=',
        height: '=',
        width: '=',
        title: '='
      },
      link: function postLink(scope, element, attrs) {
        element.html('' + scope.videoid.slug);
        console.log(scope)
        //<iframe ng-src="{{'//player.vimeo.com/video/' + document.tags.oembed_video_id.name}}" ng-width="{{document.tags.oembed_width.name}}" ng-height="{{document.tags.oembed_height.name}}" frameborder="0" title="{{document.name}}" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>
      }
    };
  });
